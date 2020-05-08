# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Plot risk of interaction per age_group
#
#
import configparser
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists, map_age_to_age_group
import statsmodels.api as sm
import matplotlib as mpl
mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['mathtext.rm'] = 'serif'
import matplotlib.pyplot as plt


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    #
    # Total patients with at least one administration
    #
    sqlp = """
        SELECT
            p.age_today,
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.age_today IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.age_today
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='age_today')
    # Map age to age_group
    dfp['age_group'] = map_age_to_age_group(dfp.index)
    # Group by age_group
    dfp = dfp.groupby('age_group').agg({'patient': 'sum'})
    #
    # Total patients with at least one coadministration
    #
    sqlc = """
        SELECT
            t.age,
            COUNT(*) as 'patient-inter'
        FROM (
            SELECT
                i.id_patient,
                i.age,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            WHERE
                i.age IS NOT NULL
            GROUP BY i.id_patient, i.age
        ) as t
        GROUP BY t.age
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='age')
    # Map age to age_group
    dfc['age_group'] = map_age_to_age_group(dfc.index)
    # Group by age_group
    dfc = dfc.groupby('age_group').agg({'patient-inter': 'sum'})

    # Concat Results
    dfr = pd.concat([dfp, dfc], axis='columns', sort='False').fillna(0)

    # Risk of CoAdministration (per age_group)
    dfr['RI^{[y1,y2]}'] = (dfr['patient-inter'] / dfr['patient'])

    print(dfr)

    #
    # Curve Fitting
    #
    y_ri = dfr['RI^{[y1,y2]}'].values
    x = np.arange(len(y_ri))
    x_ = np.linspace(x[0], x[-1], len(x) * 10)

    # RI Cubic Model
    Xi = sm.add_constant(np.column_stack([x**3, x**2, x]))
    ri_c_model = sm.OLS(y_ri, Xi)
    ri_c_model_result = ri_c_model.fit()
    # print(rc_c_model_result.summary())
    Xi_ = sm.add_constant(np.column_stack([x_**3, x_**2, x_]))
    y_ri_ = np.dot(Xi_, ri_c_model_result.params)
    ri_c_model_R2 = ri_c_model_result.rsquared_adj

    #
    # Plot
    #
    fig, ax = plt.subplots(figsize=(4.3, 3), nrows=1, ncols=1)
    ax.set_title(r'$RI^{[y_1,y_2]}$')
    #
    age_inds = np.arange(0, len(dfr))
    age_labels = dfr.index.tolist()

    # Plot
    ri, = ax.plot(age_inds, dfr['RI^{[y1,y2]}'].tolist(), marker='o', ms=6, lw=0, markerfacecolor='#ff9896', markeredgecolor='#d62728', zorder=5)

    # ri_rnd, = ax.plot(age_inds, dfN['RI^{y}_{rnd}'].values, color='red', marker='*', lw=lw, linestyle=ls, markersize=ms, zorder=6)
    # ri_rnd_, = ax.fill(np.NaN, np.NaN, 'lightpink', edgecolor='lightgray', lw=1)

    # Plot Cubic Fit
    ri_f_cubic, = ax.plot(x_, y_ri_, color='#d62728', ms=0, lw=2, zorder=3)

    # R^2
    ax.text(x=0.97, y=0.03, s=r'$R^2={:.3f}$'.format(ri_c_model_R2), ha='right', va='bottom', transform=ax.transAxes)

    # Legend
    Ls = ax.legend(
        [ri],  #, (ri_rnd_, ri_rnd) ],
        [r'$RI^{[y_1,y_2]}$'],  # , r'$RI^{[y_1,y_2]\star} [H^{rnd}_0]$' ],
        loc='upper left', handletextpad=0.5, columnspacing=0, handlelength=2, ncol=1)  #, bbox_to_anchor=(1.3, 1.125))


    ax.set_xticks(age_inds)
    ax.set_xticklabels(age_labels, rotation=90)
    ax.grid()
    #ax.set_xlim(-.6,len(age_inds)-0.4)

    # Save
    plt.tight_layout()
    wIMGfile = 'images/img-ri-age.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()
