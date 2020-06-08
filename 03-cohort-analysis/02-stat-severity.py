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
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
pd.set_option('display.precision', 2)
pd.set_option('display.float_format', lambda x: '%.2f' % x)
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
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.id_patient IN (SELECT m.id_patient FROM medication m)
    """
    patients = pd.read_sql(sqlp, con=engine).squeeze()

    #
    # Total adult patients with at least one administration
    #
    sqlap = """
        SELECT
            COUNT(*) AS 'adult-patient'
        FROM patient p
        WHERE
            p.id_patient IN (SELECT m.id_patient FROM medication m)
            AND
            p.age_today >= 20
    """
    adult_patients = pd.read_sql(sqlap, con=engine).squeeze()

    #
    # Total interactions
    #
    sqli = """
        SELECT
            i.ddi_severity,
            COUNT(*) as 'inter'
        FROM dw_interaction i
        GROUP BY i.ddi_severity
    """
    dfi = pd.read_sql(sqli, con=engine, index_col='ddi_severity')
    dfi.loc['Major & Moderate', 'inter'] = dfi.loc[['Major', 'Moderate'], 'inter'].sum()
    dfi.loc['Moderate & Minor', 'inter'] = dfi.loc[['Moderate', 'Minor'], 'inter'].sum()

    #
    # Total patients with at least one interaction
    #
    sqlpi = """
        SELECT
            t.ddi_severity,
            COUNT(DISTINCT t.id_patient) as 'patient-inter'
        FROM (
            # All rows, grouped by both patient and ddi_severity
            SELECT
                i.id_patient,
                i.ddi_severity,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            GROUP BY i.id_patient, i.ddi_severity

            UNION

            # Group rows for Major and Moderate
            SELECT
                j.id_patient,
                "Major & Moderate" AS 'ddi_severity',
                COUNT(*) AS 'inter'
            FROM dw_interaction j
            WHERE j.ddi_severity IN ('Major', 'Moderate')
            GROUP BY j.id_patient

            UNION

            # Group rows for Moderate and Minor
            SELECT
                k.id_patient,
                "Moderate & Minor" AS 'ddi_severity',
                COUNT(*) AS 'inter'
            FROM dw_interaction k
            WHERE k.ddi_severity IN ('Moderate', 'Minor')
            GROUP BY k.id_patient
        ) as t
        GROUP BY t.ddi_severity
    """
    dfpi = pd.read_sql(sqlpi, con=engine, index_col='ddi_severity')

    #
    # Total adult patients with at least one interaction
    #
    sqlpia = """
        SELECT
            t.ddi_severity,
            COUNT(*) as 'adult-patient-inter'
        FROM (
            # All rows, grouped by both patient and ddi_severity
            SELECT
                i.id_patient,
                i.ddi_severity,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            WHERE i.age >= 20
            GROUP BY i.id_patient, i.ddi_severity

            UNION

            # Group rows for Major and Moderate
            SELECT
                j.id_patient,
                "Major & Moderate" AS 'ddi_severity',
                COUNT(*) AS 'inter'
            FROM dw_interaction j
            WHERE j.ddi_severity IN ('Major', 'Moderate') AND j.age >= 20
            GROUP BY j.id_patient

            UNION

            # Group rows for Moderate and Minor
            SELECT
                k.id_patient,
                "Moderate & Minor" AS 'ddi_severity',
                COUNT(*) AS 'inter'
            FROM dw_interaction k
            WHERE k.ddi_severity IN ('Moderate', 'Minor') AND k.age >= 20
            GROUP BY k.id_patient
        ) as t
        GROUP BY t.ddi_severity
    """
    dfpia = pd.read_sql(sqlpia, con=engine, index_col='ddi_severity')

    # Concat Results
    dfr = pd.concat([dfi, dfpi, dfpia], axis='columns', sort='False').fillna(0)
    dfr.index = pd.CategoricalIndex(dfr.index, categories=['Major', 'Moderate', 'Minor', 'None', 'Major & Moderate', 'Moderate & Minor'], ordered=True)
    dfr.sort_index(inplace=True)
    # Popuation of Indy
    pop_indy_2018 = 876862  # population estimate for 2018; US Census Bureau.

    # Normalized
    dfr['patient-inter/patients'] = (dfr['patient-inter'] / patients * 100)
    dfr['patient-inter/pop'] = (dfr['patient-inter'] / pop_indy_2018 * 100)

    dfr['adult-patient-inter/adult-patients'] = (dfr['adult-patient-inter'] / adult_patients * 100)

    print(dfr)


    # Export
    wCSVfile = 'results/severity.csv'
    ensurePathExists(wCSVfile)
    dfr.to_csv(wCSVfile)
