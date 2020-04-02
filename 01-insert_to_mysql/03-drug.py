# coding=utf-8
# Author: Rion B Correia
# Date: April 01, 2020
#
# Description:
# Parses the DrugBank XML and load drugs to MySQL.
#
import configparser
import pandas as pd
import sqlalchemy
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from xml.etree import ElementTree as ET
from zipfile import ZipFile


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')

    # Truncate table
    print('Truncating Table')
    Q = engine.execute("TRUNCATE TABLE drug")

    # Init
    DEBUG = False
    ns = {'ns': 'http://www.drugbank.ca'}

    # XML
    print('Loading XML(zip) File')
    if DEBUG:
        filep = '../data/drugbank-v5.1.0/full database debug.xml'
        file = open(filep, 'r')
        version = 000

    else:
        zfilep = '../data/drugbank-v5.1.0/drugbank_all_full_database.xml.zip'
        version = 510

        zfile = ZipFile(zfilep, 'r')
        file = zfile.open('full database.xml')

    print('Parsing XML File')
    tree = ET.parse(file)
    root = tree.getroot()

    print('Version:', root.attrib['version'])
    print('Release Date:', root.attrib['exported-on'])

    #
    # Loop all drugs
    #
    r = []
    for drug in root:
        #
        # Drugs
        #
        try:
            id_drugbank = drug.find("ns:drugbank-id[@primary='true']", ns).text
        except TypeError:
            print(drug.findall('ns:drugbank-id', ns))
            continue
        id_drugbank_short = id_drugbank[2:]

        name = drug.find("ns:name", ns).text

        print('- {:s}: {:s}'.format(id_drugbank, name))

        dtype = drug.attrib['type']
        description = drug.find("ns:description", ns).text

        # Class / SubClass
        xml_classification = drug.find("ns:classification", ns)
        if xml_classification is not None:
            dclass = xml_classification.find("ns:class", ns).text
            dsubclass = xml_classification.find("ns:subclass", ns).text

        # Groups
        xml_groups = drug.find("ns:groups", ns)
        groups = []
        for xml_group in xml_groups:
            groups.append(xml_group.text)
        groups = ','.join(groups)

        r.append((id_drugbank, name, dtype, dclass, dsubclass, description, groups))
    #
    df = pd.DataFrame(r, columns=['id_drug', 'name', 'type', 'class', 'subclass', 'description', 'groups'])

    #
    # Insert to MysSQL
    #
    print('Insert to MySQL (this may take a while)')

    df.to_sql(name='drug', con=engine, if_exists='append', index=False, chunksize=500, method='multi')
