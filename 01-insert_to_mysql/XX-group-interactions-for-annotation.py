# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Reads all known interactions and extract unique ids for manual annotation of severity level.
#
#
import configparser
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)


    sql = """
        SELECT DISTINCT
            id_drug_i,
            id_drug_j,
            ANY_VALUE(name_i) AS 'name_i',
            ANY_VALUE(name_j) AS 'name_j',
            ANY_VALUE(ddi_description) AS 'description',
            ANY_VALUE(ddi_severity) AS 'severity'
        FROM dw_coadministration c
        WHERE
            c.is_ddi = TRUE
        GROUP BY id_drug_i, id_drug_j
    """
    print('Load drugs.com severity annotation')
    df = pd.read_sql(sql, con=engine, index_col=['id_drug_i', 'id_drug_j'])
    # Map Dictionary

    print('Exporting drugs.com annotation latest version')
    df.to_csv('results/drugs.com-severity.csv')

    print('Done.')
