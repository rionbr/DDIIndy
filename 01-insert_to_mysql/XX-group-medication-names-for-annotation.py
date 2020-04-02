# coding=utf-8
# Author: Rion B Correia
# Date: March 30, 2020
#
# Description: Reads all medication tables and extract unique drug names for manual annotation of DrugBank IDs.
#
#
import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

if __name__ == '__main__':

    # File Type
    ftype = 'u'

    # Map Dictionary
    print("Load Current DrugName-DrugBankID map file")
    dfM = pd.read_csv('data/map-drug-name-drugbank.csv', usecols=['ID_DRUGBANK', 'TOPIC', 'OFTALMO', 'VACCINE', 'MED_NAME'])
    dfM['MED_NAME'] = dfM['MED_NAME'].str.strip()
    # Manual Fix
    #dfM.loc[dfM['MED_NAME'] == 'protamine - EXPERIMENTAL', 'MED_NAME'] = 'protamine'
    #
    dfM.set_index('MED_NAME', inplace=True)


    print("Load Medicine Files")
    dtype = {
        'STRENGTHDOSEUNIT': 'object',
        'DISPENSEQTYUNIT': 'object',
        'DURATIONUNIT': 'object'
    }
    ldf = []
    for fid in range(1, 13):
        file = 'p2876_meds_{fid:02d}_{ftype:s}.csv'.format(fid=fid, ftype=ftype)

        # Load Data
        print('Loading Data (file: {file:s})'.format(file=file))

        dft = pd.read_csv('../data/{file:s}'.format(file=file), index_col=None, nrows=None, dtype=dtype)
        ldf.append(dft)

    print("Concatenating DataFrames")
    df = pd.concat(ldf, axis='index', ignore_index=True, verify_integrity=False)

    # PreProcessing
    print('PreProcessing')

    # Remove name left/right whitespace
    df['MED_NAME'] = df['MED_NAME'].str.strip()

    # Group by Name
    dfG = df.groupby('MED_NAME').agg({'STRENGTHDOSE': 'unique', 'STRENGTHDOSEUNIT': 'unique', 'DISPENSEQTY': 'unique', 'DISPENSEQTYUNIT': 'unique'})

    # Concatenate to map Names to DrugBankIDs
    dfF = pd.concat([dfM, dfG], axis='columns', verify_integrity=True, sort=True)
    dfF.index.name = 'MED_NAME' # Pandas 0.24.2 bug

    # List to csv
    dfF['STRENGTHDOSE'] = dfF['STRENGTHDOSE'].apply(lambda x: ','.join(str(y) for y in x))
    dfF['STRENGTHDOSEUNIT'] = dfF['STRENGTHDOSEUNIT'].apply(lambda x: ','.join(str(y) for y in x))
    dfF['DISPENSEQTY'] = dfF['DISPENSEQTY'].apply(lambda x: ','.join(str(y) for y in x))
    dfF['DISPENSEQTYUNIT'] = dfF['DISPENSEQTYUNIT'].apply(lambda x: ','.join(str(y) for y in x))

    print('Exporting dictionary latest version')
    dfF.to_csv('results/map-drug-name-drugbank.csv')

    print('Done.')
