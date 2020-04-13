# coding=utf-8
# Author: Rion B Correia
# Date: April 13, 2020
#
# Description: Computes coadministration and interaction.
#
#
import sys
import configparser
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 300)
pd.set_option('display.width', 300)
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders
from itertools import combinations
from time import sleep
from multiprocessing import Pool, Manager, cpu_count


def parallel_worker(data):
    id_patient, dfU, queue = data
    if len(dfU) == 0:
        return []
    else:
        result_user_coadmin_inter = []
        pairs = dfU['id_drug'].unique()

        for id_drug_i, id_drug_j in combinations(pairs, 2):
            # print '> %s - %s' % (db_i,db_j)

            # Order Drug Names Alphabetically
            if id_drug_i > id_drug_j:
                id_drug_i, id_drug_j = id_drug_j, id_drug_i

            dfi = dfU.loc[dfU['id_drug'] == id_drug_i, :]
            dfj = dfU.loc[dfU['id_drug'] == id_drug_j, :]

            dfi = dfi.sort_values(['dt_start', 'dt_end'], ascending=[True, False])
            dfj = dfj.sort_values(['dt_start', 'dt_end'], ascending=[True, False])

            # number of dispensations
            qt_i = dfi.shape[0]
            qt_j = dfj.shape[0]
            dfMi = pd.DataFrame.from_dict(
                {
                    'i-%s' % i: {
                        t: 1 for t in pd.date_range(r['dt_start'], r['dt_end']).tolist()
                    } for i, r in dfi.iterrows()
                }).sum(axis=1).rename(id_drug_i)
            dfMj = pd.DataFrame.from_dict(
                {
                    'j-%s' % i: {
                        t: 1 for t in pd.date_range(r['dt_start'], r['dt_end']).tolist()
                    } for i, r in dfj.iterrows()
                }).sum(axis=1).rename(id_drug_j)

            #
            dfM = pd.concat([dfMi, dfMj], axis=1).dropna(axis='index', how='all')

            counts = dfM.sum(axis=0).astype(np.int64).to_dict()

            len_i = counts[id_drug_i]
            len_j = counts[id_drug_j]

            len_ij = dfM.dropna(axis='index', how='any').shape[0]

            # No overlap
            if len_ij == 0:
                continue

            # Check if there is an interaction
            if frozenset((id_drug_i, id_drug_j)) in set_of_interactions:
                is_ddi = True
            else:
                is_ddi = False

            result_user_coadmin_inter.append(
                [id_patient, id_drug_i, id_drug_j, qt_i, qt_j, len_i, len_j, len_ij, is_ddi]
            )

        queue.put(id_patient)

        return result_user_coadmin_inter


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE coadministration")

    print('Load DB Interactions')
    sqli = "SELECT id_drug_i, id_drug_j FROM drugbank_interaction"
    dfI = pd.read_sql(sql=sqli, con=engine)
    set_of_interactions = set([frozenset((i, j)) for i, j in dfI.itertuples(index=False, name=None)])

    print('Load Dispensations')
    sqld = """
        SELECT
            md.id_medication_drug,
            m.id_medication, m.id_patient, m.dt_start, m.dt_end,
            d.id_drug, d.name
        FROM medication_drug md
            JOIN medication m ON md.id_medication = m.id_medication
            JOIN drug d ON md.id_drug = d.id_drug
        WHERE
            m.is_topic = FALSE AND
            m.is_ophthalmo = FALSE AND
            m.is_vaccine = FALSE
    """
    df = pd.read_sql(sql=sqld, con=engine)

    print('Group by id_patient')
    dfG = df.groupby('id_patient')

    #
    # Multiprocessing
    #
    n_cpu = cpu_count()
    print('Starting Multiprocess (#cpu: %d)' % (n_cpu))
    pool = Pool(n_cpu)
    manager = Manager()
    queue = manager.Queue()

    dfGList = [(id_patient, dfGU, queue) for id_patient, dfGU in dfG]

    run = pool.map_async(parallel_worker, dfGList)
    while True:
        if run.ready():
            break
        else:
            queue_size = queue.qsize()
            print('Process: {i:,d} of {total:,d} patients completed'.format(i=queue_size, total=(len(dfGList) - 1)))
            sys.stdout.flush()
            sleep(5)

    print("Processing result records")
    result_list = run.get()
    result_records = [record_list for result in result_list for record_list in result]

    # Results
    dfR = pd.DataFrame(result_records, columns=['id_patient', 'id_drug_i', 'id_drug_j', 'qt_i', 'qt_j', 'len_i', 'len_j', 'len_ij', 'is_ddi'])

    print('Insert to MySQL (this may take a while)')
    dfR.to_sql(name='coadministration', con=engine, if_exists='append', index=False, chunksize=5000, method='multi')
