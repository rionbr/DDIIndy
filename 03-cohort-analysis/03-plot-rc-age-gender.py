# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Plot risk of coadministration per age_group
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
            p.gender,
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.age_today IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.age_today, p.gender
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='age_today')
    # Map age to age_group
    dfp['age_group'] = map_age_to_age_group(dfp.index)
    # Group by age_group
    dfp = dfp.groupby(['gender', 'age_group']).agg({'patient': 'sum'})
    #
    # Total patients with at least one coadministration
    #
    sqlc = """
        SELECT
            t.age,
            t.gender,
            COUNT(*) as 'patient-coadmin'
        FROM (
            SELECT
                c.id_patient,
                c.gender,
                c.age,
                COUNT(*) AS 'coadmin'
            FROM dw_coadministration c
            WHERE
                c.age IS NOT NULL
            GROUP BY c.id_patient, c.age, c.gender
        ) as t
        GROUP BY t.age, t.gender
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='age')
    # Map age to age_group
    dfc['age_group'] = map_age_to_age_group(dfc.index)
    # Group by age_group
    dfc = dfc.groupby(['gender', 'age_group']).agg({'patient-coadmin': 'sum'})
    # Concat Results
    dfr = pd.concat([dfp, dfc], axis='columns', sort='False').fillna(0)
    # Risk of CoAdministration (per gender & age_group)
    dfr.loc[('Male', slice(None)), 'RC^{[y1,y2]}'] = dfr.loc[('Male', slice(None)), 'patient-coadmin'] / dfr.loc[('Male', slice(None)), 'patient']
    dfr.loc[('Female', slice(None)), 'RC^{[y1,y2]}'] = dfr.loc[('Female', slice(None)), 'patient-coadmin'] / dfr.loc[('Female', slice(None)), 'patient']

    print(dfr)

    #
    # Curve Fitting
    #
    """
    y_rc_m = dfr.loc[('Male', slice(None)), 'RC^{[y1,y2]}'].values
    y_rc_f = dfr.loc[('Female', slice(None)), 'RC^{[y1,y2]}'].values
    x = np.arange(len(y_rc_m))
    x_ = np.linspace(x[0], x[-1], len(x) * 10)

    # RC Cubic Model
    Xc = sm.add_constant(np.column_stack([x**3, x**2, x]))
    rc_m_c_model = sm.OLS(y_rc_m, Xc)
    rc_f_c_model = sm.OLS(y_rc_f, Xc)
    rc_m_c_model_result = rc_m_c_model.fit()
    rc_f_c_model_result = rc_f_c_model.fit()
    # print(rc_c_model_result.summary())
    Xc_ = sm.add_constant(np.column_stack([x_**3, x_**2, x_]))
    y_rc_m_ = np.dot(Xc_, rc_m_c_model_result.params)
    y_rc_f_ = np.dot(Xc_, rc_f_c_model_result.params)
    rc_m_c_model_R2 = rc_m_c_model_result.rsquared_adj
    rc_f_c_model_R2 = rc_f_c_model_result.rsquared_adj
    """
    #
    # Plot
    #
    fig, ax = plt.subplots(figsize=(4.3, 3), nrows=1, ncols=1)
    ax.set_title(r'$RC^{[y_1,y_2],g}$')
    #
    ms = 7
    lw = 1.5
    ls = '-.'
    markerfacecolor_f = '#f7b6d2'
    markerfacecolor_m = '#aec7e8'
    markeredgecolor_f = '#ff7f0e'
    markeredgecolor_m = '#ff7f0e'
    color_f = markerfacecolor_f
    color_m = markerfacecolor_m
    markeredgewidth = 1.5
    #
    age_inds = np.arange(0, len(dfr.loc[('Male', slice(None)), :]))
    age_labels = dfr.loc[('Male', slice(None)), :].index.get_level_values(level=1).tolist()

    # Plot
    rc_f, = ax.plot(
        age_inds, dfr.loc[('Female', slice(None)), 'RC^{[y1,y2]}'].tolist(),
        marker='D', ms=ms, lw=lw, ls=ls,
        color=color_f, markerfacecolor=markerfacecolor_f, markeredgecolor=markeredgecolor_f, markeredgewidth=markeredgewidth,
        zorder=5)
    rc_m, = ax.plot(
        age_inds, dfr.loc[('Male', slice(None)), 'RC^{[y1,y2]}'].tolist(),
        marker='s', ms=ms, lw=lw, ls=ls,
        color=color_m, markerfacecolor=markerfacecolor_m, markeredgecolor=markeredgecolor_m, markeredgewidth=markeredgewidth,
        zorder=5)

    # Plot Cubic Fit
    # rc_m_cubic, = ax.plot(x_, y_rc_m_, color='#ff7f0e', ms=0, lw=2, zorder=3)
    # rc_f_cubic, = ax.plot(x_, y_rc_f_, color='#ff7f0e', ms=0, lw=2, zorder=3)

    # R^2
    # ax.text(x=0.97, y=0.03, s=r'$R^2={:.3f}$'.format(rc_c_model_R2), ha='right', va='bottom', transform=ax.transAxes)

    #Legend
    ax.legend(
        [rc_f, rc_m], [r'$RC^{[y_1,y_2],F}$', r'$RC^{[y_1,y_2],M}$'],
        loc='best', handletextpad=0.5, columnspacing=0, handlelength=2, ncol=1)

    ax.set_xticks(age_inds)
    ax.set_xticklabels(age_labels, rotation=90)
    ax.grid()
    #ax.set_xlim(-.6,len(age_inds)-0.4)

    # Save
    plt.tight_layout()
    wIMGfile = 'images/img-rc-age-gender.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()
