# coding=utf-8
# Author: Rion B Correia
# Date: May 13, 2020
#
# Description: Computed drug pair probabilities and measures
#
#
import configparser
import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists
from collections import OrderedDict


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
    patients_male = dfp.loc['Male', 'patient']
    patients_female = dfp.loc['Female', 'patient']
    patients = patients_male + patients_female

    #
    # Load Drugs Administrations
    #
    sqld = """
        SELECT
            md.id_drug,
            COUNT(DISTINCT p.id_patient) as 'patient-drug'
        FROM medication_drug md
        JOIN medication m ON md.id_medication = m.id_medication
        JOIN patient p ON m.id_patient = p.id_patient
        GROUP BY md.id_drug
    """
    dfd = pd.read_sql(sqld, con=engine, index_col='id_drug')
    #
    # Load Coadministrations
    #
    sqli = """
        SELECT
            i.id_patient,
            i.gender,
            i.id_drug_i,
            i.id_drug_j,
            i.name_i,
            i.name_j,
            di.class AS "class_i",
            dj.class AS "class_j",
            i.len_i,
            i.len_j,
            i.len_ij,
            i.is_ddi,
            i.ddi_description,
            i.ddi_severity
        FROM dw_interaction i
        JOIN drug di ON i.id_drug_i = di.id_drug
        JOIN drug dj ON i.id_drug_j = dj.id_drug
    """
    dfi = pd.read_sql(sqli, con=engine, index_col=None)

    # Calculate Tau
    dfi['tau'] = dfi['len_ij'] / (dfi['len_i'] + dfi['len_j'] - dfi['len_ij'])

    #
    # Groupby drug i & j
    #
    dfig = dfi.groupby(['id_drug_i', 'id_drug_j']).agg(
        OrderedDict([
            ('id_patient', pd.Series.nunique),
            ('gender', {'female': lambda x: (x == 'Female').sum(), 'male': lambda x: (x == 'Male').sum()}),
            ('name_i', 'first'),
            ('name_j', 'first'),
            ('len_i', 'sum'),
            ('len_j', 'sum'),
            ('len_ij', ['sum', 'mean', 'std']),
            ('class_i', 'first'),
            ('class_j', 'first'),
            ('ddi_description', 'first'),
            ('ddi_severity', 'first'),
            ('tau', 'sum')
        ]))

    # Because pandas < 0.24
    dfig.columns = pd.Index([
        "{prefix:s}({name:s})".format(name=name, prefix=prefix) if prefix not in ['nunique', 'first'] else "{name:s}".format(name=name)
        for name, prefix in dfig.columns.to_flat_index()
    ])
    dfig.rename(columns={
        'id_patient': 'patient',
        'female(gender)': 'patient-female',
        'male(gender)': 'patient-male',
    }, inplace=True)

    # Include drug info
    dfig['patient-drug_i'] = dfig.index.get_level_values(level=0).map(dfd['patient-drug'])
    dfig['patient-drug_j'] = dfig.index.get_level_values(level=1).map(dfd['patient-drug'])

    # Compute Gamma
    dfig['gamma_drug_ij'] = dfig['patient'] / dfig['patient-drug_i']
    dfig['gamma_drug_ji'] = dfig['patient'] / dfig['patient-drug_j']

    # normalized tau
    dfig['tau-norm'] = dfig['sum(tau)'] / dfig['patient']

    # Join probability
    dfig['P(inter,male)'] = dfig['patient-male'] / patients
    dfig['P(inter,female)'] = dfig['patient-female'] / patients
    # Conditional probability
    dfig['P(inter|male)'] = dfig['P(inter,male)'] / patients_male
    dfig['P(inter|female)'] = dfig['P(inter,female)'] / patients_female
    # Relative Risks
    dfig['RRI_{ij}^{female}'] = dfig['P(inter|female)'] / dfig['P(inter|male)']
    dfig['RRI_{ij}^{male}'] = dfig['P(inter|male)'] / dfig['P(inter|female)']

    # Ranks
    dfig['rank(patient)'] = dfig['patient'].rank(method='min', ascending=False).astype(int)
    dfig['rank(tau-norm)'] = dfig['tau-norm'].rank(method='min', ascending=False).astype(int)
    dfig['rankprod(tau,patient)'] = dfig['rank(tau-norm)'] * dfig['rank(patient)']

    # Sort
    dfig.sort_values('rankprod(tau,patient)', ascending=True, inplace=True)

    #
    # Export
    #
    wCSVfile = 'results/interactions.csv.gz'
    ensurePathExists(wCSVfile)
    dfig.to_csv(wCSVfile)
