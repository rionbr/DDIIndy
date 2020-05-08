# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: Inserts `drugbank-interaction.csv` and `drugs.com-severity.csv` to MySQL.
#
#
import configparser
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
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE drugbank_interaction")

    # Load Interactions
    dfI = pd.read_csv('data/drugbank-interaction.csv.gz', index_col=None, usecols=['label', 'interaction'])

    # Split Label string 'DB0001 DB0002' into tuple ('DB0001', 'DB00002')
    def split_drugbank_ids(x):
        i, j = tuple(x.split(' '))
        if i > j:
            i, j = j, i
        return pd.Series({'id_drug_i': i, 'id_drug_j': j})

    dfI[['id_drug_i', 'id_drug_j']] = dfI['label'].apply(split_drugbank_ids)
    dfI.drop('label', axis='columns', inplace=True)


    #
    # Update a few IDs to match old drugbank. These ids are secondary ids.
    #
    # Rauwolfia serpentina root
    dfI.loc[(dfI['id_drug_i'] == 'DB00386'), 'id_drug_i'] = 'DB09363'
    dfI.loc[(dfI['id_drug_j'] == 'DB00386'), 'id_drug_j'] = 'DB09363'
    # Valproic Acid
    dfI.loc[(dfI['id_drug_i'] == 'DB00510'), 'id_drug_i'] = 'DB00313'
    dfI.loc[(dfI['id_drug_j'] == 'DB00510'), 'id_drug_j'] = 'DB00313'
    # Ergoloid mesylate
    dfI.loc[(dfI['id_drug_i'] == 'DB01287'), 'id_drug_i'] = 'DB01049'
    dfI.loc[(dfI['id_drug_j'] == 'DB01287'), 'id_drug_j'] = 'DB01049'
    # Bismuth
    dfI.loc[(dfI['id_drug_i'] == 'DB01294'), 'id_drug_i'] = 'DB01402'
    dfI.loc[(dfI['id_drug_j'] == 'DB01294'), 'id_drug_j'] = 'DB01402'
    # Insulin glargine
    dfI.loc[(dfI['id_drug_i'] == 'DB01308'), 'id_drug_i'] = 'DB00047'
    dfI.loc[(dfI['id_drug_j'] == 'DB01308'), 'id_drug_j'] = 'DB00047'
    # Insulin lispro
    dfI.loc[(dfI['id_drug_i'] == 'DB01310'), 'id_drug_i'] = 'DB00046'
    dfI.loc[(dfI['id_drug_j'] == 'DB01310'), 'id_drug_j'] = 'DB00046'
    # Doxacurium
    dfI.loc[(dfI['id_drug_i'] == 'DB01334'), 'id_drug_i'] = 'DB01135'
    dfI.loc[(dfI['id_drug_j'] == 'DB01334'), 'id_drug_j'] = 'DB01135'
    # Troleandomycin
    dfI.loc[(dfI['id_drug_i'] == 'DB01361'), 'id_drug_i'] = 'DB13179'
    dfI.loc[(dfI['id_drug_j'] == 'DB01361'), 'id_drug_j'] = 'DB13179'
    # Salicylic acid
    dfI.loc[(dfI['id_drug_i'] == 'DB01398'), 'id_drug_i'] = 'DB00936'
    dfI.loc[(dfI['id_drug_j'] == 'DB01398'), 'id_drug_j'] = 'DB00936'
    # Belladona
    dfI.loc[(dfI['id_drug_i'] == 'DB01617'), 'id_drug_i'] = 'DB13913'
    dfI.loc[(dfI['id_drug_j'] == 'DB01617'), 'id_drug_j'] = 'DB13913'
    # Ribavirin
    dfI.loc[(dfI['id_drug_i'] == 'DB01693'), 'id_drug_i'] = 'DB00811'
    dfI.loc[(dfI['id_drug_j'] == 'DB01693'), 'id_drug_j'] = 'DB00811'

    #
    dfI.set_index(['id_drug_i', 'id_drug_j'], inplace=True)
    dfI = dfI.loc[~dfI.index.duplicated(keep='first'), :]

    # Load Severity Score
    dfS = pd.read_csv('data/drugs.com-severity.csv', index_col=['id_drug_i', 'id_drug_j'])

    # Combine DFs
    df = pd.concat([dfI, dfS['severity']], axis='columns')

    print('Insert to MySQL')
    df.rename(columns={
        'interaction': 'description'
    }, inplace=True)
    df.reset_index(inplace=True)
    #
    df.to_sql(name='drugbank_interaction', con=engine, if_exists='append', index=False, chunksize=1, method='multi')
