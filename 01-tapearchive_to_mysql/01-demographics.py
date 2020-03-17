# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: Inserts `p2876_demographics.csv` to MySQL
#
#
import configparser
import numpy as np
import pandas as pd
import sqlalchemy


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    query = engine.execute("SELECT 1+1")

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE patient")

    # Load Data
    print('Loading Data')
    df = pd.read_csv('../data/p2876_demographics.csv', index_col=None, nrows=10, dtype={'ZIP': str})

    # PreProcessing
    print('PreProcessing')

    # DOB
    df['DOB'] = pd.to_datetime(df['DOB'], format='%Y-%m-%d')

    # Gender
    df['GENDER'] = df['GENDER'].replace(
        {
            'Male': 1,
            'Female': 2
        })

    # Ethnicity
    df['ETHNICITY'] = df['ETHNICITY'].replace(
        {
            'Not Hispanic or Latino': 1,
            'Not Hispanic, Latino/a, or Spanish Origin': 2,
            'Hispanic or Latino': 3,
            'Unknown': 99,
            'Unreported/Refused to Report': 99,
            'Declined': 99
        })
    # Race
    df['RACE'] = df['RACE'].replace(
        {
            # White
            'White': 1,
            'CAUCASIAN': 1,
            # Black/AA
            'Black or African American': 2,
            # Hispanic
            'HISPANIC': 3,
            # Asian
            'Asian': 4,
            'Other Asian': 4,
            # Native
            'American Indian or Alaska Native': 5,
            # Islander
            'Other Pacific Islander': 6,
            'Native Hawaiian or Other Pacific Islande': 6,
            # >1 Race
            'More than one race': 10,
            'BI-RACIAL': 10,
            # Other
            'Unknown': 99,
            'Refused': 99,
            'Unreported/Refused to report race': 99,
            'Decline to Answer': 99,
        })

    # Zip
    def preprocessing_zip(x):
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

    #
    def preprocessing_split_zip(x):
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

    df['ZIP'] = df['ZIP'].apply(preprocessing_zip)
    df[['ZIP5', 'ZIP4']] = df['ZIP'].apply(preprocessing_split_zip)
    df.drop('ZIP', axis='columns', inplace=True)

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
    df = df.loc[:, ['id_patient', 'dob', 'ethnicity', 'race', 'zip5', 'zip4']]
    df.to_sql(name='patient', con=engine, if_exists='append', index=False, chunksize=1000, method='multi')
