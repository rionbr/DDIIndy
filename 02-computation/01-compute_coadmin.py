# coding=utf-8
# Author: Rion B Correia
# Date: April 13, 2020
#
# Description: Computes coadministration and interaction.
#
#
import configparser
import pandas as pd
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 300)
pd.set_option('display.width', 300)
import swifter
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders
from itertools import combinations
from time import sleep
from datetime import datetime
import multiprocessing as mp


url = ''
set_of_interactions = set()
worker_data = []


def parallel_overlap_worker(row, dfD):
    id_drug_i = row['id_drug_i']
    id_drug_j = row['id_drug_j']
    # Order Drug Names Alphabetically
    if id_drug_i > id_drug_j:
        id_drug_i, id_drug_j = id_drug_j, id_drug_i

    dfi = dfD.loc[dfD['id_drug'] == id_drug_i, :]
    dfj = dfD.loc[dfD['id_drug'] == id_drug_j, :]

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

    counts = dfM.sum(axis=0).astype(int).to_dict()

    len_i = counts[id_drug_i]
    len_j = counts[id_drug_j]

    len_ij = dfM.dropna(axis='index', how='any').shape[0]

    # Check if there is an interaction
    if frozenset((id_drug_i, id_drug_j)) in set_of_interactions:
        is_ddi = True
    else:
        is_ddi = False

    return pd.Series({'qt_i': qt_i, 'qt_j': qt_j, 'len_i': len_i, 'len_j': len_j, 'len_ij': len_ij, 'is_ddi': is_ddi})


def parallel_query_worker(data):
    id_patient, queue = data
    dt_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Worker engine
    worker_engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(worker_engine, "before_cursor_execute", add_own_encoders)

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
            m.is_vaccine = FALSE AND
            m.id_patient = {id_patient:d}
    """.format(id_patient=id_patient)

    dfD = pd.read_sql(sql=sqld, con=worker_engine)

    # Return earlier if no dispensation for this patient
    if len(dfD) <= 1:
        # Add Parsed Patient
        dt_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        sql = "INSERT INTO helper_patient_parsed (id_patient, dt_start, dt_end) VALUES ({id_patient:d}, '{dt_start:s}', '{dt_end:s}')".\
            format(id_patient=id_patient, dt_start=dt_start, dt_end=dt_end)
        worker_engine.execute(sql)
        worker_engine.dispose()
        # Queue
        queue.put(id_patient)
        return 0
    else:

        unique_drugs = dfD['id_drug'].unique().tolist()
        # Combination ij
        pairs_drugs = combinations(unique_drugs, 2)
        # id_i < id_j
        pairs_drugs = [(id_drug_i, id_drug_j) if (id_drug_i < id_drug_j) else (id_drug_j, id_drug_i) for id_drug_i, id_drug_j in pairs_drugs]
        # to DataFrame
        dfij = pd.DataFrame(pairs_drugs, columns=['id_drug_i', 'id_drug_j'])
        dfij['id_patient'] = id_patient

        # Calculates Overlap
        dfO = dfij.swifter.progress_bar(enable=False).apply(parallel_overlap_worker, axis='columns', args=(dfD, ))

        # Result DataFrame
        dfR = pd.concat([dfij, dfO], axis='columns', sort=False)

        # Insert to MySQL
        dfR = dfR.loc[:, ['id_patient', 'id_drug_i', 'id_drug_j', 'qt_i', 'qt_j', 'len_i', 'len_j', 'len_ij', 'is_ddi']]
        dfR.to_sql(name='coadministration', con=worker_engine, if_exists='append', index=False, chunksize=500, method='multi')

        # Add Parsed Patient
        dt_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        sql = "INSERT INTO helper_patient_parsed (id_patient, dt_start, dt_end) VALUES ({id_patient:d}, '{dt_start:s}', '{dt_end:s}')".\
            format(id_patient=id_patient, dt_start=dt_start, dt_end=dt_end)
        worker_engine.execute(sql)
        worker_engine.dispose()
        # Queue
        queue.put(id_patient)
        return len(dfR)


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    print('Load DB Interactions')
    sqli = "SELECT id_drug_i, id_drug_j FROM drugbank_interaction"
    dfI = pd.read_sql(sql=sqli, con=engine)
    set_of_interactions = set([frozenset((i, j)) for i, j in dfI.itertuples(index=False, name=None)])

    # Truncate table
    # print('Truncating Table')
    # Q = engine.execute("TRUNCATE TABLE coadministration")
    # Q = engine.execute("TRUNCATE TABLE helper_patient_parsed")

    print('Load Patient IDs')
    sqlp = """
        SELECT
            p.id_patient
        FROM patient p
        WHERE
            p.id_patient NOT IN (
                SELECT DISTINCT hp.id_patient FROM helper_patient_parsed hp
            )
    """
    dfP = pd.read_sql(sql=sqlp, con=engine)

    #
    # MultiProcessing
    #
    n_cpu = mp.cpu_count()
    print('Starting Multiprocess (#cpu: %d)' % (n_cpu))
    n_tasks = dfP.shape[0]
    pool = mp.Pool(n_cpu)
    manager = mp.Manager()
    queue = manager.Queue()

    # Worker Data
    worker_data = [(id_patient, queue) for id_patient in dfP['id_patient'].tolist()]

    run = pool.map_async(parallel_query_worker, worker_data)

    while True:
        if run.ready():
            break
        else:
            size = queue.qsize()
            print("Process: {i:,d} of {n:,d} completed".format(i=size, n=n_tasks))
            sleep(60)

    result_list = run.get()

    pool.close()
    pool.join()

    print('Done.')
