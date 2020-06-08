# coding=utf-8
# Author: Rion B Correia
# Date: May 13, 2020
#
# Description: Builds the DDI network.
#
#
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
from sklearn.preprocessing import MinMaxScaler
import networkx as nx
import matplotlib as mpl
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from utils import ensurePathExists


if __name__ == '__main__':

    dfd = pd.read_csv('../02-computation/results/drugs.csv.gz', index_col='id_drug')
    dfi = pd.read_csv('../02-computation/results/interactions.csv.gz', index_col=['id_drug_i', 'id_drug_j'])

    # Load Drugs.com Classes
    dfclass = pd.read_csv('../01-insert_to_mysql/data/drugs.com-classes.csv', index_col='id_drug')
    # Update drug classes
    dfi['class_i'] = dfi.index.get_level_values(level=0).map(dfclass['class'].to_dict())
    dfi['class_j'] = dfi.index.get_level_values(level=1).map(dfclass['class'].to_dict())

    #
    # Build Network
    #
    female_hormones = {
        'DB00783': 'Estradiol',
        'DB00977': 'Ethinylestradiol',
        'DB00717': 'Norethisterone',
        'DB00603': 'Medroxyprogesterone acetate',
        'DB00304': 'Desogestrel',
        'DB00367': 'Levonorgestrel',
        'DB00286': 'Conjugated estrogens',
    }

    # Set INF values to the MAX
    maxrrivalue = dfi[['RRI_{ij}^{female}', 'RRI_{ij}^{male}']].replace([np.inf, -np.inf], np.nan).max().max().round(2)
    #
    dfi.loc[dfi['RRI_{ij}^{female}'] == np.inf, 'RRI_{ij}^{female}'] = maxrrivalue
    dfi.loc[dfi['RRI_{ij}^{male}'] == np.inf, 'RRI_{ij}^{male}'] = maxrrivalue

    # ReScale Weight Values
    scaler = MinMaxScaler(feature_range=(1, 15))
    dfi['scaler(patient)'] = scaler.fit_transform(dfi['patient'].values.reshape(-1, 1))
    scaler = MinMaxScaler(feature_range=(1, 10))
    dfi['scaler(tau-norm)'] = scaler.fit_transform(dfi['tau-norm'].values.reshape(-1, 1))

    #
    # RRI Color (same code used to plot colorbar)
    #
    N = 64
    norm = mpl.colors.Normalize(vmin=1, vmax=5)
    #
    darkred = '#d62728'
    lightred = '#fae9e9'
    darkblue = '#1f77b4'
    lightblue = '#e8f1f7'
    gray = '#7f7f7f'
    #
    cmap_female = mpl.colors.LinearSegmentedColormap.from_list('female', colors=[lightred, darkred], N=N)
    cmap_male = mpl.colors.LinearSegmentedColormap.from_list('male', colors=[lightblue, darkblue], N=N)
    #
    cmap_female.set_under(gray)
    cmap_male.set_under(gray)
    #
    cmap_female.set_over(darkred)
    cmap_male.set_over(darkblue)

    dict_color = {
        'CNS agents': '#9467bd',  # '#976fb0' #purple
        'Anti-infectives': '#2ca02c',  # '#66c059' #green
        'Cardiovascular agents': '#d62728',  # '#ee262c' #red
        'Psychotherapeutic agents': '#e377c2',  # '#c059a2' #pink
        'Hormones': '#e7ba52',  # '#f2ea25' #yellow
        'Metabolic agents': '#ff7f0e',  # '#f47a2b', #orange
        'Respiratory agents': '#1f77b4',  # '#4da9df', #blue
        'Gastrointestinal agents': '#bcbd22',  # '#6c8b37', #vomit
        'Antineoplastics': '#7f7f7f',  # gray
        'Genitourinary tract agents': '#8c564b',  # brown
        'Miscellaneous agents': '#cedb9c',  # light green
        'Nutritional products': '#17becf',  # '#b4e2ee', #cyan
        'Immunologic agents': '#7b4173',  # darkpink
        'Coagulation modifiers': '#843c39',  # blood
        'Radiologic agents': '#9c9ede',  # lightblue
    }
    dict_prob_inter = dfd['P(inter)'].to_dict()

    # Builds Networkx Graph
    G = nx.Graph()

    for (id_drug_i, id_drug_j), row in dfi.iterrows():
        # Node
        name_i = row['name_i']
        name_j = row['name_j']
        class_i = row['class_i']
        class_j = row['class_j']
        hormone_i = True if id_drug_i in female_hormones else False
        hormone_j = True if id_drug_j in female_hormones else False

        # Female
        if row['RRI_{ij}^{female}'] > 1.0:
            gender = 'Female'
            rri = row['RRI_{ij}^{female}']
            edge_color_rbg = cmap_female(norm(rri))
        elif row['RRI_{ij}^{male}'] < 1.0:
            gender = 'Male'
            rri = row['RRI_{ij}^{male}']
            edge_color_rbg = cmap_male(norm(rri))
        else:
            raise Exception("RRI exactly 1.0?")

        edge_color_hex = mpl.colors.rgb2hex(edge_color_rbg)

        if not G.has_node(id_drug_i):
            color_i = dict_color.get(class_i, 'white')
            prob_inter = dict_prob_inter[id_drug_i]
            dict_node = {
                'label': name_i,
                'class': class_i,
                'color': color_i,
                'prob_inter': prob_inter,
                'hormone': hormone_i
            }
            G.add_node(id_drug_i, **dict_node)

        if not G.has_node(id_drug_j):
            color_j = dict_color.get(class_j, 'white')
            prob_inter = dict_prob_inter[id_drug_j]
            dict_node = {
                'label': name_j,
                'class': class_j,
                'color': color_j,
                'prob_inter': prob_inter,
                'hormone': hormone_j
            }
            G.add_node(id_drug_j, **dict_node)

        # Edges
        G.add_edge(id_drug_i, id_drug_j, **{
            'RRI_{ij}^{female}': row['RRI_{ij}^{female}'],
            'RRI_{ij}^{male}': row['RRI_{ij}^{male}'],
            'severity': row['ddi_severity'],
            #
            'patient': row['patient'],
            'patient_scaler': row['scaler(patient)'],
            #
            'tau': row['tau-norm'],
            'tau_scaler': row['scaler(tau-norm)'],
            #
            'color': edge_color_hex,
            'gender': gender})

    G_patient = G.copy()
    G_tau = G.copy()

    #
    # Set weight 
    #
    nx.set_edge_attributes(G_patient, nx.get_edge_attributes(G, 'patient_scaler'), 'weight')
    nx.set_edge_attributes(G_tau, nx.get_edge_attributes(G, 'tau_scaler'), 'weight')

    #
    # Export
    #
    wGtauFile = 'results/ddi_network_tau.gpickle'
    ensurePathExists(wGtauFile)
    nx.write_gpickle(G_tau, wGtauFile)
    nx.write_graphml(G_tau, 'results/ddi_network_tau.graphml')
    #
    wGpatientFile = 'results/ddi_network_patient.gpickle'
    ensurePathExists(wGpatientFile)
    nx.write_gpickle(G_patient, wGpatientFile)
