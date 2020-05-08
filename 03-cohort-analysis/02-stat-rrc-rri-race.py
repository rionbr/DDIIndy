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
from utils import add_own_encoders  # , ensurePathExists


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
            p.race,
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.race IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.race
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='race')

    #
    # Total patients with at least one coadministration
    #
    sqlc = """
        SELECT
            t.race,
            COUNT(*) as 'patient-coadmin'
        FROM (
            SELECT
                c.id_patient,
                c.race,
                COUNT(*) AS 'coadmin'
            FROM dw_coadministration c
            WHERE
                c.race IS NOT NULL
            GROUP BY c.id_patient, c.race
        ) as t
        GROUP BY t.race
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='race')

    #
    # Total patients with at least one interaction
    #
    sqli = """
        SELECT
            t.race,
            COUNT(*) as 'patient-inter'
        FROM (
            SELECT
                i.id_patient,
                i.race,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            WHERE
                i.race IS NOT NULL
            GROUP BY i.id_patient, i.race
        ) as t
        GROUP BY t.race
    """
    dfi = pd.read_sql(sqli, con=engine, index_col='race')

    # Concat Results
    dfr = pd.concat([dfp, dfc, dfi], axis='columns', sort='False').fillna(0)

    # Relative Risk of CoAdministration (per race)
    dfr['RRC^{race}'] = (dfr['patient-coadmin'] / dfr['patient']) / (dfr.loc['White', 'patient-coadmin'] / dfr.loc['White', 'patient'])

    # Relative Risk of Interaction (per race)
    dfr['RRI^{race}'] = (dfr['patient-inter'] / dfr['patient']) / (dfr.loc['White', 'patient-inter'] / dfr.loc['White', 'patient'])

    print(dfr)
