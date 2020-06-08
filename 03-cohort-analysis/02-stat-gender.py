# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Statistis about relative risk of coadministration and interaction
#
#
import configparser
# import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    #
    # Total patients with at least one administration
    #
    sqlp = """
        SELECT
            p.gender,
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.gender IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.gender
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='gender')

    #
    # Total patients with at least one coadministration
    #
    sqlc = """
        SELECT
            t.gender,
            COUNT(*) as 'patient-coadmin'
        FROM (
            SELECT
                c.id_patient,
                c.gender,
                COUNT(*) AS 'coadmin'
            FROM dw_coadministration c
            WHERE
                c.gender IS NOT NULL
            GROUP BY c.id_patient, c.gender
        ) as t
        GROUP BY t.gender
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='gender')

    #
    # Total patients with at least one interaction
    #
    sqli = """
        SELECT
            t.gender,
            COUNT(*) as 'patient-inter'
        FROM (
            SELECT
                i.id_patient,
                i.gender,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            WHERE
                i.gender IS NOT NULL
            GROUP BY i.id_patient, i.gender
        ) as t
        GROUP BY t.gender
    """
    dfi = pd.read_sql(sqli, con=engine, index_col='gender')

    # Concat Results
    dfr = pd.concat([dfp, dfc, dfi], axis='columns', sort='False').fillna(0)

    # Relative Risk of CoAdministration (per gender)
    dfr['RRC^{g=F}'] = (dfr['patient-coadmin'] / dfr['patient']) / (dfr.loc['Male', 'patient-coadmin'] / dfr.loc['Male', 'patient'])

    # Relative Risk of Interaction (per gender)
    dfr['RRI^{g=F}'] = (dfr['patient-inter'] / dfr['patient']) / (dfr.loc['Male', 'patient-inter'] / dfr.loc['Male', 'patient'])

    print(dfr)

    # Export
    wCSVfile = 'results/gender.csv'
    ensurePathExists(wCSVfile)
    dfr.to_csv(wCSVfile)

