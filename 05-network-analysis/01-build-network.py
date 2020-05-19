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

    #
    # Build Network
    #
    female_hormones = ['Ethinyl Estradiol', 'Estradiol', 'Norethisterone', 'Levonorgestrel', 'Estrogens Conj.']

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
    n = int(256 / 32)
    bounds = np.arange(0, 6, 1)
    boundaries = np.linspace(0.6, 5, n * 32).tolist()[2:-2] + [5.2, 5.6]
    reds = mpl.cm.Reds(np.linspace(0.2, 0.8, n * 12))
    grays = np.array([mpl.colors.to_rgba('gray')] * n * 3)
    blues = mpl.cm.Blues(np.linspace(0.2, 0.8, n * 12))
    colors_male = np.vstack((grays, blues))
    colors_female = np.vstack((grays, reds))
    cmap_male = LinearSegmentedColormap.from_list('nx', colors=colors_male)
    cmap_female = LinearSegmentedColormap.from_list('nx', colors=colors_female)
    cmap_male.set_over(blues[-1])  # 'yellow')
    cmap_male.set_under('gray')  # 'gray')
    cmap_female.set_over(reds[-1])  # 'yellow')
    cmap_female.set_under('gray')
    norm = mpl.colors.Normalize(vmin=0, vmax=5)

    dict_color = {
        'Cardiovascular agents': '#ee262c',
        'CNS agents': '#976fb0',
        'Hormones': '#f2ea25',
        'Anti-infectives': '#66c059',
        'Psychotherapeutic agents': '#c059a2',
        'Metabolic agents': '#f47a2b',
        'Respiratory agents': '#4da9df',
        'Gastrointestinal agents': '#6c8b37',
        'Nutritional Products': '#b4e2ee',
        'Topical Agents': '#ffe5cc',
        'Coagulation modifiers': '#f498b7',
        #
        'None': '#c7c7c7',
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
        hormone_i = True if name_i in female_hormones else False
        hormone_j = True if name_j in female_hormones else False

        # Female
        if row['RRI_{ij}^{female}'] > 1.0:
            gender = 'Female'
            rri = row['RRI_{ij}^{female}']
            edge_color_rbg = cmap_female(norm(rri))
        else:
            gender = 'Male'
            rri = row['RRI_{ij}^{male}']
            edge_color_rbg = cmap_male(norm(rri))

        edge_color_hex = mpl.colors.rgb2hex(edge_color_rbg)

        if not G.has_node(id_drug_i):
            color_i = dict_color[class_i]
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
            color_j = dict_color[class_j]
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
            'RRI^F': row['RRI_{ij}^{female}'],
            'RRI^M': row['RRI_{ij}^{male}'],
            'severity': row['ddi_severity'],
            #
            'patients': row['patient'],
            'patients_norm': row['scaler(patient)'],
            #
            'tau': row['tau-norm'],
            'tau_scaler': row['scaler(tau-norm)'],
            #
            'color': edge_color_hex,
            'gender': gender})


    G_patient   = G.copy()
    G_tau = G.copy()

    #
    # Set weight 
    #
    nx.set_edge_attributes(G_patient, nx.get_edge_attributes(G, 'patients_norm'), 'weight')
    nx.set_edge_attributes(G_tau, nx.get_edge_attributes(G, 'tau_norm'), 'weight')

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
