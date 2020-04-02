# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: Inserts `p2876_demographics.csv` to MySQL.
#
#
import configparser
import numpy as np
import pandas as pd
import sqlalchemy


def preprocessing_zip(x):
    """ Preprocesses the raw ZIP field"""
    # Null
    if pd.isnull(x):
        return np.nan
    #
    if len(x) == 10:
        # Remove empty zeros '12345-0000'
        if x[-4:] == '0000':
            x = x[:5]
    #
    if len(x) == 9:
        # Split into '12345-1234' if '123451234'
        x = x[:5] + '-' + x[-4:]
    return x


def preprocessing_split_zip(x):
    """ Separates ZIP codes '47408-1234' into ('47408', '1234') """
    # Null
    if pd.isnull(x):
        return pd.Series({'ZIP': np.nan, 'ZIP+4': np.nan})
    #
    xl = x.split('-')
    zip5 = xl[0]
    if len(xl) == 1:
        zip4 = None
    else:
        zip4 = xl[1]
    return pd.Series({'ZIP': zip5, 'ZIP4': zip4})


def handle_duplicated_patients(dfg):
    if len(dfg) > 1:
        # DOB
        vc_dob = dfg['DOB'].value_counts()
        dob = vc_dob.index[0] if len(vc_dob) else None
        # Gender
        vc_gender = dfg['GENDER'].value_counts()
        gender = vc_gender.index[0] if len(vc_gender) else None
        # Ethnicity
        vc_ethnicity = dfg['ETHNICITY'].value_counts()
        ethnicity = vc_ethnicity.index[0] if len(vc_ethnicity) else None
        # Race
        vc_race = dfg['RACE'].value_counts()
        race = vc_race.index[0] if len(vc_race) else None
        # ZIP5
        vc_zip5 = dfg['ZIP5'].value_counts()
        zip5 = vc_zip5.index[0] if len(vc_zip5) else None
        # ZIP4
        vc_zip4 = dfg['ZIP4'].value_counts()
        zip4 = vc_zip4.index[0] if len(vc_zip4) else None
        #
        return pd.Series({
            'STUDY_ID': int(dfg['STUDY_ID'].iloc[0]),
            'DOB': dob,
            'GENDER': gender,
            'ETHNICITY': ethnicity,
            'RACE': race,
            'ZIP5': zip5,
            'ZIP4': zip4
        }).to_frame().T
    else:
        return dfg


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE patient")

    # Load Data
    print('Loading Data')
    df = pd.read_csv('../data/p2876_demographics.csv', index_col=None, nrows=None, dtype={'ZIP': str})

    # PreProcessing
    print('PreProcessing')

    # DOB
    df['DOB'] = pd.to_datetime(df['DOB'], format='%Y-%m-%d')

    # Gender
    """
    df['GENDER'] = df['GENDER'].replace(
        {
            'Male': 1,
            'Female': 2
        })
    """

    # Ethnicity
    df['ETHNICITY'] = df['ETHNICITY'].replace(
        {
            'Not Hispanic or Latino': 'Not Hispanic/Latino',
            'Not Hispanic, Latino/a, or Spanish Origin': 'Not Hispanic/Latino/Spanish',
            'Hispanic or Latino': 'Hispanic/Latino',
            'Unknown': 'Unknown',
            'Unreported/Refused to Report': 'Unknown',
            'Declined': 'Unknown'
        })

    # Race
    df['RACE'] = df['RACE'].replace(
        {
            # White
            'White': 'White',
            'CAUCASIAN': 'White',
            # Black/AA
            'Black or African American': 'Black',
            # Hispanic
            'HISPANIC': 'Hispanic',
            # Asian
            'Asian': 'Asian',
            'Other Asian': 'Asian',
            # Native
            'American Indian or Alaska Native': 'Indian',
            # Islander
            'Other Pacific Islander': 'Islander',
            'Native Hawaiian or Other Pacific Islande': 'Islander',
            # >1 Race
            'More than one race': 'Bi-racial',
            'BI-RACIAL': 'Bi-racial',
            # Other
            'Unknown': 'Unknown',
            'Refused': 'Unknown',
            'Unreported/Refused to report race': 'Unknown',
            'Decline to Answer': 'Unknown',
        })

    # Zip
    df['ZIP'] = df['ZIP'].apply(preprocessing_zip)
    df[['ZIP5', 'ZIP4']] = df['ZIP'].apply(preprocessing_split_zip)
    df.drop('ZIP', axis='columns', inplace=True)

    # Handle duplicates
    df = df.groupby('STUDY_ID').apply(handle_duplicated_patients)
    df.reset_index(drop=True, inplace=True)

    #
    print('Insert to MySQL (this may take a while)')
    df.rename(columns={
        'STUDY_ID': 'id_patient',
        'DOB': 'dob',
        'GENDER': 'gender',
        'ETHNICITY': 'ethnicity',
        'RACE': 'race',
        'ZIP5': 'zip5',
        'ZIP4': 'zip4'
    }, inplace=True)
    df = df.loc[:, ['id_patient', 'dob', 'gender', 'ethnicity', 'race', 'zip5', 'zip4']]
    df.to_sql(name='patient', con=engine, if_exists='append', index=False, chunksize=1, method='multi')
