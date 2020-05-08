# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Plot risk of interaction per age_group
#
#
import configparser
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists, map_age_to_age_group
from itertools import combinations
import random
import swifter

np.random.seed(1)


def apply_null_model_interactions(row, set_available_drugs, set_interactions):
    n_unique_drugs = row['n_unique_drugs']
    n_coadmin = row['n_coadmin']
    #
    if (n_coadmin == 0 or n_unique_drugs == 0):
        return 0
    else:
        # Sample Drugs
        sample_drugs = random.sample(set_available_drugs, n_unique_drugs)
        # Possible Coadmins
        all_possible_coadmin = list(combinations(sample_drugs, 2))
        # Sample Possible Coadmins based on patient n_coadmin
        sample_coadmin = random.sample(all_possible_coadmin, n_coadmin)
        # Which are DDI
        inter = [frozenset(coadmin) in set_interactions for coadmin in sample_coadmin]
        # Number of interactions found
        return sum(inter)



if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    #
    # All Drug Interactions
    #
    print("Load drug-drug interactions")
    sqli = """
        SELECT DISTINCT
            dbi.id_drug_i,
            dbi.id_drug_j,
            dbi.severity
        FROM drugbank_interaction dbi
    """
    dfi = pd.read_sql(sqli, con=engine, index_col=['id_drug_i', 'id_drug_j'])
    set_interactions = set([frozenset(index) for index, row in dfi.iterrows()])
    #
    # Drugs available per age group
    #
    print("Load drugs available per age group")
    sqld = """
        SELECT
            d.id_drug, d.name, p.age_today
        FROM medication_drug md
            JOIN medication m ON m.id_medication = md.id_medication
            JOIN drug d ON d.id_drug = md.id_drug
            JOIN patient p ON m.id_patient = p.id_patient
        WHERE 
            m.is_topic = FALSE AND
            m.is_ophthalmo = FALSE AND
            m.is_vaccine = FALSE
        GROUP BY
            d.id_drug, p.age_today
    """
    dfd = pd.read_sql(sqld, con=engine, index_col='id_drug')
    # Map age to age_group
    dfd['age_group'] = map_age_to_age_group(dfd['age_today'])

    #
    # Patients
    #
    print("Load patients (n_drugs/n_coadmin)")
    sqlp = """
        SELECT
            p.id_patient,
            p.gender,
            p.age_today,
            p.race,
            p.zip4,
            nd.n_unique_drugs,
            nc.n_coadmin
        FROM patient p
        JOIN
            # Number of Unique Drugs
            (
                SELECT tmp.id_patient, COUNT(1) AS 'n_unique_drugs'
                FROM (
                    SELECT m.id_patient, md.id_drug
                    FROM medication_drug md
                        JOIN medication m ON md.id_medication = m.id_medication
                    GROUP BY m.id_patient, md.id_drug
                ) AS tmp GROUP BY tmp.id_patient
            ) AS nd ON nd.id_patient = p.id_patient
        JOIN
            # Number of CoAdministrations
            (
                SELECT co.id_patient, COUNT(1) as 'n_coadmin'
                FROM coadministration co
                GROUP BY co.id_patient
            ) AS nc ON nc.id_patient = p.id_patient
        WHERE
            p.id_patient IN (SELECT m.id_patient FROM medication m)
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='id_patient')
    # Map age to age_group
    dfp['age_group'] = map_age_to_age_group(dfp['age_today'])

    #
    #
    #
    n_runs = 100
    qt_sample_multiplier = 1.0
    results = []
    for age_group, dfpt in dfp.groupby('age_group'):
        print("-- Computing age_group: {age_group:s}".format(age_group=age_group))

        if len(dfpt) < 10:
            continue
        # Drugs in this age_range
        dfdt = dfd.loc[(dfd['age_group'] == age_group), :]
        set_available_drugs = set(dfdt.index.to_list())

        for run in range(1, (n_runs + 1)):
            print("> run: {run:d}".format(run=run))

            # Number of samples
            n_user_samples = int(len(dfpt) * qt_sample_multiplier)
            # Sample Users
            dfpts = dfpt.sample(n=n_user_samples, replace=True)
            dfpts['zip4'] = dfpts['zip4'].fillna(value=0).astype(int)

            # Compute interactions from random prescription
            dfpts['n_inter'] = dfpts.swifter.apply(apply_null_model_interactions, args=(set_available_drugs, set_interactions), axis='columns')

            # Variables to groupby
            dfpts['age_group'] = age_group
            dfpts['run'] = run
            dfpts['patients'] = 1
            dfpts['patients_with_ddi'] = dfpts['n_inter'].apply(bool)

            dfres = dfpts.groupby(['gender', 'race', 'zip4']).agg({
                'age_group': 'first',
                'run': 'first',
                'patients': 'sum',
                'patients_with_ddi': 'sum'
            })

            # Append DF
            results.append(dfres)

    # Concatenate result DataFrames
    print("Concatenate results")
    dfR = pd.concat(results)

    # Export
    print("Exporting")
    dfR.to_csv('results/age_gender_race_zip_null_model.csv.gz')
