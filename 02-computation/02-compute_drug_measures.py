# coding=utf-8
# Author: Rion B Correia
# Date: May 18, 2020
#
# Description: Computes individual drug probabilities and measures
#
#
import configparser
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
import swifter
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists
from sklearn.preprocessing import MinMaxScaler
from collections import OrderedDict


def calc_drug_probabilities(id_drug, engine):
    sqlt = """
        SELECT id_drug_i, id_drug_j, name_i, name_j, id_patient, is_ddi
        FROM dw_coadministration
        WHERE (id_drug_i = '{id_drug:s}' OR id_drug_j = '{id_drug:s}')
    """.format(id_drug=id_drug)
    #
    dfct = pd.read_sql(sqlt, con=engine, index_col=None)
    dfit = dfct.loc[dfct['is_ddi'] == True, :]
    #
    coadmin = len(dfct)
    inter = len(dfit)
    patient = len(dfct['id_patient'].unique())
    patient_inter = len(dfit['id_patient'].unique())
    return pd.Series({'id_drug': id_drug, 'coadmin': coadmin, 'inter': inter, 'patient': patient, 'patient-inter': patient_inter})


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    #
    # Calculate PI(i), probability of a single drug to interact when co-administered with another
    #
    sqld = """
        SELECT d.id_drug
        FROM drug d
        WHERE d.id_drug in (SELECT md.id_drug FROM medication_drug md)
    """
    dfd = pd.read_sql(sqld, con=engine)

    # Loop through Coadmin and Computes numbers
    dfr = dfd['id_drug'].swifter.apply(calc_drug_probabilities, args=(engine, ))
    # Probability of interaction
    dfr['P(inter)'] = dfr['inter'] / dfr['coadmin']
    dfr['P(patient-inter)'] = dfr['patient-inter'] / dfr['patient']

    #
    # Export
    #
    wCSVfile = 'results/drugs.csv.gz'
    ensurePathExists(wCSVfile)
    dfr.to_csv(wCSVfile)
