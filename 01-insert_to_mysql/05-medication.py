# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: Inserts `p2876_meds_{d}_u.csv` to MySQL.
#
#
import configparser
import numpy as np
import pandas as pd
import sqlalchemy
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def calculates_date_end(r):
    start = r['ORDERING_DATE']
    duration = r['DURATION']
    unit = r['DURATIONUNIT']

    # If no duration, assume one single day of treatment
    if pd.isnull(duration) or pd.isnull(unit):
        return start + pd.Timedelta(value=1, unit='day')

    if unit == 'Minutes':
        timedelta = pd.Timedelta(value=duration, unit='minutes')
    elif unit == 'Hours':
        timedelta = pd.Timedelta(value=duration, unit='hours')
    elif unit == 'Days':
        timedelta = pd.Timedelta(value=duration, unit='days')
    elif unit == 'Weeks':
        timedelta = pd.Timedelta(value=duration * 7, unit='days')
    elif unit == 'Months':
        timedelta = pd.Timedelta(value=duration * 30, unit='days')
    ##
    elif unit == 'Treatments':
            timedelta = pd.Timedelta(value=duration, unit='days')
    elif unit == 'Doses':
            timedelta = pd.Timedelta(value=duration, unit='days')
    elif unit == 'Times':
            timedelta = pd.Timedelta(value=duration, unit='days')
    #
    return start + timedelta


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE medication")
    Q = engine.execute("TRUNCATE TABLE medication_drug")

    # File Type
    ftype = 'u'

    # Map Dictionary
    dfD = pd.read_csv('data/map-drug-name-drugbank.csv', usecols=['ID_DRUGBANK', 'TOPIC', 'OPHTHALMO', 'VACCINE', 'MED_NAME'], na_values='None')
    dfD['MED_NAME'] = dfD['MED_NAME'].str.strip()
    dfD['ID_DRUGBANK'] = dfD['ID_DRUGBANK'].str.strip()
    dfD.dropna(subset=['ID_DRUGBANK'], inplace=True)
    dfDd = dfD.copy()
    
    # Unique Index
    dfD.set_index('MED_NAME', inplace=True)

    # Duplicated Index
    n_ids = []
    n_data = []
    dfDd['ID_DRUGBANK'] = dfDd['ID_DRUGBANK'].str.split(',')
    dfDd = dfDd.set_index('ID_DRUGBANK')
    for (ids, data) in zip(dfDd.index, dfDd.values):
        if isinstance(ids, list):
            for id in ids:
                n_ids.append(id)
                n_data.append(data)
        else:
            n_ids.append(ids)
            n_data.append(data)
    dfDd = pd.DataFrame.from_records(data=n_data, index=pd.Series(n_ids, name='ID_DRUG'), columns=['TOPIC', 'OPHTHALMO', 'VACCINE', 'MED_NAME'])
    dfDd = dfDd.reset_index().set_index('MED_NAME')

    print("Load Medicine Files")
    dtype = {
        'STRENGTHDOSEUNIT': 'object',
        'DISPENSEQTYUNIT': 'object',
        'DURATIONUNIT': 'object'
    }
    ldf = []
    for fid in range(1, 13):
        file = 'p2876_meds_{fid:02d}_{ftype:s}.csv'.format(fid=fid, ftype=ftype)

        # Load Data
        print('Loading Data (file: {file:s})'.format(file=file))

        dft = pd.read_csv('../data/{file:s}'.format(file=file), index_col=None, nrows=None, dtype=dtype)
        ldf.append(dft)
        #break

    print("Concatenating DataFrames")
    dfM = pd.concat(ldf, axis='index', ignore_index=True, verify_integrity=False)
    dfM['ID_MEDICATION'] = np.arange(1, len(dfM) + 1)
    # PreProcessing
    print('PreProcessing')

    # Catalog CVCD
    dfM['CATALOGCVCD'] = dfM['CATALOGCVCD'].astype(int)

    # Order Date
    dfM['ORDERING_DATE'] = pd.to_datetime(dfM['ORDERING_DATE'], format='%Y-%m-%d')

    dfM['END_DATE'] = dfM[['ORDERING_DATE', 'DURATION', 'DURATIONUNIT']].apply(calculates_date_end, axis='columns')

    """
    dfM['ORDER_STATUS'] = dfM['ORDER_STATUS'].replace({
        'Sent': 1,
        'Ordered': 2,
        'Completed': 3,
        'Discontinued': 99
    })
    """

    # Dose Strength
    dfM['STRENGTHDOSE'] = pd.to_numeric(dfM['STRENGTHDOSE'].str.replace(',', ''))

    # Dose Strength Unit
    dfM['STRENGTHDOSEUNIT'] = dfM['STRENGTHDOSEUNIT'].replace({
        'Unit(s)': 'Units'
    })

    # Quantity dispensed
    dfM['DISPENSEQTY'] = pd.to_numeric(dfM['DISPENSEQTY'].str.replace(',', ''))

    # Quantity dispensed unit
    dfM['DISPENSEQTYUNIT'] = dfM['DISPENSEQTYUNIT'].replace({
        'packet(s)': 'Packet',
    })

    # Remove name left/right whitespace
    dfM['MED_NAME'] = dfM['MED_NAME'].str.strip()

    # Left Join TOPIC, OPHTHALMO, VACCINE
    dfM = dfM.join(dfD[['TOPIC', 'OPHTHALMO', 'VACCINE']].fillna(False), on='MED_NAME', how='left')
    #
    # Medication-Drug
    #
    # Inner Join (medication_drug)
    dfMD = dfM.set_index('MED_NAME')[['ID_MEDICATION']].join(dfDd[['ID_DRUG']], on='MED_NAME', how='inner')
    dfMD['ID_MEDICATION_DRUG'] = np.arange(1, len(dfMD) + 1)
    dfMD.sort_values('ID_MEDICATION_DRUG').reset_index(inplace=True, drop=True)

    #
    # Insert to MysSQL
    #
    print('Insert to MySQL (this may take a while)')

    # dfM
    print('> dfM')
    dfM.rename(columns={
        'ID_MEDICATION': 'id_medication',
        'STUDY_ID': 'id_patient',
        'ORDERING_DATE': 'dt_start',
        'END_DATE': 'dt_end',
        'ORDER_STATUS': 'status',
        'MED_NAME': 'name',
        'CATALOGCVCD': 'id_catalog',
        'STRENGTHDOSE': 'dose_strength',
        'STRENGTHDOSEUNIT': 'dose_strength_unit',
        'DISPENSEQTY': 'qt_dispensed',
        'DISPENSEQTYUNIT': 'qt_dispensed_unit',
        'REFILLQTY': 'qt_refill',
        'NBRREFILLS': 'nr_refill',
        'DURATION': 'duration',
        'DURATIONUNIT': 'duration_unit',
        'TOPIC': 'is_topic',
        'OPHTHALMO': 'is_ophthalmo',
        'VACCINE': 'is_vaccine',
    }, inplace=True)
    cols = [
        'id_medication', 'id_patient', 'id_catalog',
        'dt_start', 'dt_end', 'status', 'name', 'dose_strength', 'dose_strength_unit', 'qt_dispensed', 'qt_dispensed_unit', 'qt_refill', 'nr_refill', 'duration', 'duration_unit',
        'is_topic', 'is_ophthalmo', 'is_vaccine'
    ]
    dfM = dfM.loc[:, cols]
    dfM.to_sql(name='medication', con=engine, if_exists='append', index=False, chunksize=5000, method='multi')

    # dfD
    print('> dfMD')
    dfMD.rename(columns={
        'ID_MEDICATION_DRUG': 'id_medication_drug',
        'ID_MEDICATION': 'id_medication',
        'ID_DRUG': 'id_drug'
    }, inplace=True)
    dfMD.to_sql(name='medication_drug', con=engine, if_exists='append', index=False, chunksize=5000, method='multi')

    #
    print('Done.')
