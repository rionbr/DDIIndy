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
from utils import add_own_encoders, ensurePathExists, map_age_to_age_group


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
            p.age_today,
            p.gender,
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.age_today IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.age_today, p.gender
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='age_today')
    # Map age to age_group
    dfp['age_group'] = map_age_to_age_group(dfp.index)
    # Group by age_group
    dfp = dfp.groupby(['gender', 'age_group']).agg({'patient': 'sum'})

    #
    # Total patients with at least one coadministration
    #
    sqlc = """
        SELECT
            t.age,
            t.gender,
            COUNT(*) as 'patient-coadmin'
        FROM (
            SELECT
                c.id_patient,
                c.gender,
                c.age,
                COUNT(*) AS 'coadmin'
            FROM dw_coadministration c
            WHERE
                c.age IS NOT NULL
            GROUP BY c.id_patient, c.age, c.gender
        ) as t
        GROUP BY t.age, t.gender
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='age')
    # Map age to age_group
    dfc['age_group'] = map_age_to_age_group(dfc.index)
    # Group by age_group
    dfc = dfc.groupby(['gender', 'age_group']).agg({'patient-coadmin': 'sum'})

    #
    # Total patients with at least one DDI
    #
    sqli = """
        SELECT
            t.age,
            t.gender,
            COUNT(*) as 'patient-inter'
        FROM (
            SELECT
                i.id_patient,
                i.gender,
                i.age,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            WHERE
                i.age IS NOT NULL
            GROUP BY i.id_patient, i.age, i.gender
        ) as t
        GROUP BY t.age, t.gender
    """
    dfi = pd.read_sql(sqli, con=engine, index_col='age')
    # Map age to age_group
    dfi['age_group'] = map_age_to_age_group(dfi.index)
    # Group by age_group
    dfi = dfi.groupby(['gender', 'age_group']).agg({'patient-inter': 'sum'})

    # Concat Results
    dfr = pd.concat([dfp, dfc, dfi], axis='columns', sort='False').fillna(0)

    # Risk of CoAdministration (per gender & age_group)
    dfr.loc[('Male', slice(None)), 'RC^{[y1,y2]}'] = dfr.loc[('Male', slice(None)), 'patient-coadmin'] / dfr.loc[('Male', slice(None)), 'patient']
    dfr.loc[('Female', slice(None)), 'RC^{[y1,y2]}'] = dfr.loc[('Female', slice(None)), 'patient-coadmin'] / dfr.loc[('Female', slice(None)), 'patient']

    # Risk of Interaction (per gender & age_group)
    dfr.loc[('Male', slice(None)), 'RI^{[y1,y2]}'] = dfr.loc[('Male', slice(None)), 'patient-inter'] / dfr.loc[('Male', slice(None)), 'patient']
    dfr.loc[('Female', slice(None)), 'RI^{[y1,y2]}'] = dfr.loc[('Female', slice(None)), 'patient-inter'] / dfr.loc[('Female', slice(None)), 'patient']

    print(dfr)

    # Export
    wCSVfile = 'results/age-gender.csv'
    ensurePathExists(wCSVfile)
    dfr.to_csv(wCSVfile)
