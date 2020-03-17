# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: Inserts `p2876_meds_01_t.csv` to MySQL.
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
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    query = engine.execute("SELECT 1+1")

    # File Type
    ftype = 'u'

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE medication_{ftype:s}".format(ftype=ftype))


    for fid in range(1, 13):
        file = 'p2876_meds_{fid:02d}_{ftype:s}.csv'.format(fid=fid, ftype=ftype)

        # Load Data
        print('Loading Data (file: {file:s})'.format(file=file))
        dtype = {
            'STRENGTHDOSEUNIT': 'object',
            'DISPENSEQTYUNIT': 'object',
            'DURATIONUNIT': 'object'
        }
        df = pd.read_csv('../data/{file:s}'.format(file=file), index_col=None, nrows=None, dtype=dtype)

        # PreProcessing
        print('PreProcessing')

        # 't' doesn't have Catalog ID; 'u' doesn't have NDC
        if ftype == 't':
            df['CATALOGCVCD'] = np.nan
        elif ftype == 'u':
            df['CATALOGCVCD'] = df['CATALOGCVCD'].astype(int)
            df['NDC'] = np.nan

        # Order Date
        df['ORDERING_DATE'] = pd.to_datetime(df['ORDERING_DATE'], format='%Y-%m-%d')

        df['ORDER_STATUS'] = df['ORDER_STATUS'].replace({
            'Sent': 1,
            'Ordered': 2,
            'Completed': 3,
            'Discontinued': 99
        })

        # Dose Strength
        df['STRENGTHDOSE'] = pd.to_numeric(df['STRENGTHDOSE'].str.replace(',',''))

        df['STRENGTHDOSEUNIT'] = df['STRENGTHDOSEUNIT'].replace({
            'Unit(s)': 'Units'
        })

        df['DISPENSEQTY'] = pd.to_numeric(df['DISPENSEQTY'].str.replace(',',''))

        df['DISPENSEQTYUNIT'] = df['DISPENSEQTYUNIT'].replace({
            'packet(s)': 'Packet',
        })

        print('Insert to MySQL (this may take a while)')
        df.rename(columns={
            'STUDY_ID': 'id_patient',
            'ORDERING_DATE': 'dt_order',
            'ORDER_STATUS': 'status',
            'MED_NAME': 'name',
            'CATALOGCVCD': 'id_catalog',
            'NDC': 'ndc',
            'STRENGTHDOSE': 'dose_strength',
            'STRENGTHDOSEUNIT': 'dose_strength_unit',
            'DISPENSEQTY': 'qt_dispensed',
            'DISPENSEQTYUNIT': 'qt_dispensed_unit',
            'REFILLQTY': 'qt_refill',
            'NBRREFILLS': 'nr_refill',
            'DURATION': 'duration',
            'DURATIONUNIT': 'duration_unit'
        }, inplace=True)
        df = df.loc[:, ['id_patient', 'id_catalog', 'ndc', 'dt_order', 'status', 'name', 'dose_strength', 'dose_strength_unit', 'qt_dispensed', 'qt_dispensed_unit', 'qt_refill', 'nr_refill', 'duration', 'duration_unit']]
        df.to_sql(name='medication_{ftype}'.format(ftype=ftype), con=engine, if_exists='append', index=False, chunksize=1, method='multi')

    print('Done.')