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


def parallel_query_worker(data):
    id_patient, queue = data
    worker_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Worker engine
    engine = sqlalchemy.create_engine(url, pool_size=24, max_overflow=0, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

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

    dfD = pd.read_sql(sql=sqld, con=engine)

    # Return earlier if no dispensation for this patient
    if len(dfD) <= 1:
        # Add Parsed Patient
        worker_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        sql = "INSERT INTO helper_patient_parsed (id_patient, dt_start, dt_end) VALUES ({id_patient:d}, '{dt_start:s}', '{dt_end:s}')".\
            format(id_patient=id_patient, dt_start=worker_start, dt_end=worker_end)
        engine.execute(sql)
        engine.dispose()
        # Queue
        queue.put(id_patient)
        return 0
    else:

        # Results
        r = []

        # Calculate Intervals
        dfD['interval'] = dfD.apply(lambda r: pd.Interval(r['dt_start'], r['dt_end'], closed='both'), axis='columns')

        # Loop combination of all rows
        for (i, j) in list(combinations(dfD.index, 2)):
            # .at is faster than .loc
            id_drug_i = dfD.at[i, 'id_drug']
            id_drug_j = dfD.at[j, 'id_drug']
            #
            if id_drug_i > id_drug_j:
                i, j = j, i
                id_drug_i, id_drug_j = id_drug_j, id_drug_i
            #
            id_medication_drug_i = dfD.at[i, 'id_medication_drug']
            id_medication_drug_j = dfD.at[j, 'id_medication_drug']
            #
            interval_i = dfD.at[i, 'interval']
            interval_j = dfD.at[j, 'interval']

            # There is administration overlap
            if interval_i.overlaps(interval_j):

                # Overlap length/start/end
                length = min(interval_i.right - interval_j.left, interval_j.right - interval_i.left).days + 1
                dt_start = max(interval_i.left, interval_j.left)
                dt_end = min(interval_i.right, interval_j.right)

                # Is this coadministration DDI
                if frozenset((id_drug_i, id_drug_j)) in set_of_interactions:
                    is_ddi = True
                else:
                    is_ddi = False
                r.append((id_patient, id_medication_drug_i, id_medication_drug_j, id_drug_i, id_drug_j, dt_start, dt_end, length, is_ddi))

        # Insert to MySQL
        if len(r):
            dfR = pd.DataFrame(r, columns=['id_patient', 'id_medication_drug_i', 'id_medication_drug_j', 'id_drug_i', 'id_drug_j', 'dt_start', 'dt_end', 'length', 'is_ddi'])
            dfR.to_sql(name='coadmin', con=engine, if_exists='append', index=False, chunksize=5000, method='multi')

        # Add Parsed Patient
        worker_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        sql = "INSERT INTO helper_patient_parsed (id_patient, dt_start, dt_end) VALUES ({id_patient:d}, '{dt_start:s}', '{dt_end:s}')".\
            format(id_patient=id_patient, dt_start=worker_start, dt_end=worker_end)
        engine.execute(sql)
        engine.dispose()
        # Queue
        queue.put(id_patient)
        return 1


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, pool_size=1, max_overflow=0, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    print('Load DB Interactions')
    sqli = "SELECT id_drug_i, id_drug_j FROM drugbank_interaction"
    dfI = pd.read_sql(sql=sqli, con=engine)
    set_of_interactions = set([frozenset((i, j)) for i, j in dfI.itertuples(index=False, name=None)])

    # Truncate table
    # print('Truncating Table')
    # Q = engine.execute("TRUNCATE TABLE coadministration")
    # Q = engine.execute("TRUNCATE TABLE helper_patient_parsed")
    for loop in range(25):
        print('Load Patient IDs - loop {loop:d}'.format(loop=loop))
        sqlp = """
            SELECT
                p.id_patient
            FROM patient p
            WHERE
                p.id_patient NOT IN (
                    SELECT DISTINCT hp.id_patient FROM helper_patient_parsed hp
                )
            LIMIT 50000
        """
        dfP = pd.read_sql(sql=sqlp, con=engine)

        if len(dfP):
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

    engine.dispose()
    print('Done.')
