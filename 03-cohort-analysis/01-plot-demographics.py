# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Demographics
#
#
import configparser
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists, map_age_to_age_group
import matplotlib as mpl
mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['mathtext.rm'] = 'serif'
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import to_hex
from matplotlib.colors import LinearSegmentedColormap


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    #
    # Retrieve Data
    #

    #
    # Gender (only from those with a medication)
    #
    sqlg = """
        SELECT
            p.gender,
            COUNT(*) AS 'count'
        FROM patient p
        WHERE
            p.gender IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.gender
    """
    dfg = pd.read_sql(sqlg, con=engine, index_col='gender')
    # Percent
    dfg['%'] = dfg['count'] / dfg['count'].sum()
    # Color
    dfg.loc['Male', 'color'] = '#1f77b4'
    dfg.loc['Female', 'color'] = '#d62728'

    # Age (today; only from those with a medication)
    sqla = """
        SELECT
            p.age_today AS 'age',
            COUNT(*) AS 'count'
        FROM patient p
        WHERE
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.age_today
    """
    dfa = pd.read_sql(sqla, con=engine, index_col='age')
    # Map age to age_group
    dfa['age_group'] = map_age_to_age_group(dfa.index)
    # Group by age_group
    dfa = dfa.groupby('age_group').agg({'count': 'sum'})
    # Percent
    dfa['%'] = dfa['count'] / dfa['count'].sum()
    # Color
    #cmap = LinearSegmentedColormap.from_list(name='custom', colors=['#ff7f0e', '#d62728', '#9467bd'], N=256, gamma=1.0)
    cmap = cm.get_cmap('jet_r')
    dfa['color'] = [to_hex(cmap(c)) for c in np.linspace(0, 1, len(dfa))]

    #
    # Ethnicity
    #
    sqle = """
        SELECT
            p.ethnicity,
            COUNT(*) AS 'count'
        FROM patient p
        WHERE
            /* p.ethnicity IS NOT NULL AND */
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.ethnicity
    """
    dfe = pd.read_sql(sqle, con=engine)
    # Rename 
    dfe['ethnicity'] = dfe.replace({'Hispanic/Latino': 'Hispanic/Latino', 'Not Hispanic, Latino/a, or Spanish origin': 'Not Hisp/Latin/Span', 'Not Hispanic/Latino': 'Not Hisp/Latin'})
    dfe['ethnicity'] = dfe['ethnicity'].fillna('n/a')
    # To Categorical
    dfe['ethnicity'] = pd.Categorical(dfe['ethnicity'], categories=['Not Hisp/Latin', 'Not Hisp/Latin/Span', 'Hisp/Latin', 'n/a'], ordered=True)
    # Sort
    dfe = dfe.sort_values('ethnicity', ascending=True)
    # Set Index
    dfe.set_index('ethnicity', inplace=True)
    # %
    dfe['%'] = dfe['count'] / dfe['count'].sum()
    # Color
    dfe['color'] = ['#ffbb78', '#c49c94', '#98df8a', '#c7c7c7']

    # Race
    sqlr = """
        SELECT
            p.race,
            count(*) AS 'count'
        FROM patient p
        WHERE
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.race
    """
    dfr = pd.read_sql(sqlr, con=engine)
    # Rename / Group
    race_minorities = 'Bi-racial, Hispanic, Islander, or Indian'
    dfr['race'] = dfr['race'].replace({'Islander': 'Minorities', 'Bi-racial': 'Minorities', 'Hispanic': 'Minorities', 'Indian': 'Minorities'})
    dfr['race'] = dfr['race'].fillna('n/a')
    dfr = dfr.groupby('race').agg('sum').reset_index()
    # To Categorical
    dfr['race'] = pd.Categorical(dfr['race'], categories=['White', 'Black', 'Asian', 'Minorities', 'Indian', 'Islander', 'Bi-racial', 'Hispanic', 'n/a'], ordered=True)
    # Sort
    dfr = dfr.sort_values('race', ascending=True)
    # Set Index[]
    dfr.set_index('race', inplace=True)
    # %
    dfr['%'] = dfr['count'] / dfr['count'].sum()
    # Color
    dfr['color'] = ['#ff7f0e', '#8c564b', '#e377c2', '#17becf', '#c7c7c7']

    #
    # Plot
    #
    fig, ax = plt.subplots(figsize=(7, 2.5), nrows=1, ncols=1)
    ax.set_title('Patient Demographics')

    width = 0.80
    edgecolor = '#7f7f7f'

    # Gender
    cum_percent = 0
    for gender, row in dfg.iterrows():
        percent = row['%']
        facecolor = row['color']
        b = ax.barh(2, percent, width, facecolor=facecolor, left=cum_percent, edgecolor=edgecolor, alpha=0.5)
        #
        patch = b.get_children()[0]
        bx, by = patch.get_xy()
        tx, ty = 0.5 * patch.get_width() + bx, 0.45 * patch.get_height() + by
        #
        ax.text(tx, ty, gender, ha='center', va='center', rotation=0)
        #
        cum_percent += percent

    # Age
    cum_percent = 0
    for age_group, row in dfa.iterrows():
        percent = row['%']
        facecolor = row['color']
        b = ax.barh(1, percent, width, facecolor=facecolor, left=cum_percent, edgecolor=edgecolor, alpha=0.5)
        #
        patch = b.get_children()[0]
        bx, by = patch.get_xy()
        tx, ty = 0.59 * patch.get_width() + bx, 0.5 * patch.get_height() + by
        #
        if age_group not in ['80-84', '85-89', '90-94', '95-99', '>99']:
            ax.text(tx, ty, age_group, ha='center', va='center', rotation=90)
        #
        cum_percent += percent

    # Race
    cum_percent = 0
    for race, row in dfr.iterrows():
        percent = row['%']
        facecolor = row['color']
        b = ax.barh(0, percent, width, facecolor=facecolor, left=cum_percent, edgecolor=edgecolor, alpha=0.5)
        #
        patch = b.get_children()[0]
        bx, by = patch.get_xy()
        tx, ty = 0.5 * patch.get_width() + bx, 0.45 * patch.get_height() + by
        #
        if race in ['White', 'Black']:
            ax.text(tx, ty, race, ha='center', va='center', rotation=0)
        elif race == 'Minorities':
            mx, my = 0.58, -1.1
            ax.annotate(race_minorities, xy=(tx, 0.25 * patch.get_height() + by), xycoords='data', xytext=(mx, my),
                arrowprops=dict(facecolor='black', arrowstyle="<|-,head_length=0.3,head_width=0.15",
                connectionstyle="angle3,angleA=0,angleB=90"),
                horizontalalignment='left', verticalalignment='center'
                )
        else:
            ax.text(tx, ty, race, ha='center', va='center', rotation=90)

        #
        cum_percent += percent

    # Ethnicity
    """
    cum_percent = 0
    for ethnicity, row in dfe.iterrows():
        percent = row['%']
        color = row['color']
        b = ax.barh(0, percent, width, color=color, left=cum_percent, edgecolor=edgecolor)
        #
        patch = b.get_children()[0]
        bx, by = patch.get_xy()
        tx, ty = 0.5 * patch.get_width() + bx, 0.45 * patch.get_height() + by
        #
        if ethnicity in ['Hisp/Latin']:
            ax.text(tx, ty, ethnicity, ha='center', va='center', rotation=90)
        else:
            pass
        #
        cum_percent += percent
    """

    #
    xticks = np.linspace(0, 1, 11, endpoint=True)
    xticklabels = ['%.1f' % x for x in xticks]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    yticks = np.array([0, 1, 2]). # + (width / 2)
    ax.set_yticks(yticks)
    ax.set_yticklabels(['Race', 'Age', 'Gender'])

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 2.5)

    # Save
    plt.subplots_adjust(left=0.10, right=0.97, bottom=0.20, top=0.88, wspace=0, hspace=0)
    wIMGfile = 'images/img-demographics.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()