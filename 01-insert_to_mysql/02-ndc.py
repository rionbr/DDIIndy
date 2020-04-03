# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: Inserts `p2876_ndc.csv` to MySQL.
#
#
import configparser
import pandas as pd
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    query = engine.execute("SELECT 1+1")
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE ndc")

    # Load Data
    file = 'p2876_ndc.csv'
    print('Loading Data (file: {file:s})'.format(file=file))
    dtype = {}
    df = pd.read_csv('../data/{file:s}'.format(file=file), index_col=None, nrows=None, dtype=dtype)

    print('Insert to MySQL (this may take a while)')
    df.rename(columns={
        'CATALOGCVCD': 'id_catalog',
        'NDC': 'ndc',
    }, inplace=True)
    df = df.loc[:, ['id_catalog', 'ndc']]
    df.to_sql(name='ndc', con=engine, if_exists='append', index=False, chunksize=1000, method='multi')
