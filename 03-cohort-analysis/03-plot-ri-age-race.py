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
            p.race,
            COUNT(*) AS 'patient'
        FROM patient p
        WHERE
            p.age_today IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.age_today, p.race
    """
    dfp = pd.read_sql(sqlp, con=engine, index_col='age_today')
    # Map age to age_group
    dfp['age_group'] = map_age_to_age_group(dfp.index)
    # Group by age_group
    dfp = dfp.groupby(['race', 'age_group']).agg({'patient': 'sum'})
    #
    # Total patients with at least one DDI
    #
    sqli = """
        SELECT
            t.age,
            t.race,
            COUNT(*) as 'patient-inter'
        FROM (
            SELECT
                i.id_patient,
                i.race,
                i.age,
                COUNT(*) AS 'inter'
            FROM dw_interaction i
            WHERE
                i.age IS NOT NULL
            GROUP BY i.id_patient, i.age, i.race
        ) as t
        GROUP BY t.age, t.race
    """
    dfi = pd.read_sql(sqli, con=engine, index_col='age')
    # Map age to age_group
    dfi['age_group'] = map_age_to_age_group(dfi.index)
    # Group by age_group
    dfi = dfi.groupby(['race', 'age_group']).agg({'patient-inter': 'sum'})

    # Concat Results
    dfr = pd.concat([dfp, dfi], axis='columns', sort='False').fillna(0)

    # Risk of Interaction (per race & age_group)
    dfr = dfr.loc[(['White', 'Black'], slice(None)), :].copy()
    dfr.loc[('White', slice(None)), 'RI^{[y1,y2]}'] = dfr.loc[('White', slice(None)), 'patient-inter'] / dfr.loc[('White', slice(None)), 'patient']
    dfr.loc[('Black', slice(None)), 'RI^{[y1,y2]}'] = dfr.loc[('Black', slice(None)), 'patient-inter'] / dfr.loc[('Black', slice(None)), 'patient']

    print(dfr)

    #
    # Random Null Model
    #
    dfn = pd.read_csv('results/age_gender_race_zip_null_model.csv.gz')
    # Group by 'age_group' and 'run'
    dfn = dfn.groupby(['race','age_group', 'run']).agg({'patients': 'sum', 'patients_with_ddi': 'sum'})
    #
    dfn = dfn.loc[(['White', 'Black'], slice(None), slice(None)), :].copy()
    # Group by 'age_group' and compute confidence interval
    dfng = pd.DataFrame({
        'patients': dfn.groupby(['race', 'age_group'])['patients'].apply(calc_confidence_interval),
        'patients_with_ddi': dfn.groupby(['race', 'age_group'])['patients_with_ddi'].apply(calc_confidence_interval)
    }).unstack()
    # Compute RI (for mean, ci-max and ci-min)
    dfng[('RI^{[y1,y2]}_{rnd}', 'mean')] = (dfng[('patients_with_ddi', 'mean')] / dfng[('patients', 'mean')])
    dfng[('RI^{[y1,y2]}_{rnd}', 'ci95-max')] = (dfng[('patients_with_ddi', 'ci95-max')] / dfng[('patients', 'mean')])
    dfng[('RI^{[y1,y2]}_{rnd}', 'ci95-min')] = (dfng[('patients_with_ddi', 'ci95-min')] / dfng[('patients', 'mean')])

    #
    # Curve Fitting
    #
    """
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
    """
    #
    # Plot
    #
    fig, ax = plt.subplots(figsize=(4.3, 3), nrows=1, ncols=1)
    ax.set_title(r'$RI^{[y_1,y_2],r}$')
    #
    ms = 7
    lw = 1.5
    ls = '-.'
    markerfacecolor_w = '#98df8a'
    markerfacecolor_b = '#c49c94'
    markeredgecolor_w = '#d62728'
    markeredgecolor_b = '#d62728'
    color_w = markeredgecolor_w
    color_b = markeredgecolor_b
    markeredgewidth = 1.5
    #
    age_inds = np.arange(0, len(dfr.loc[('White', slice(None)), :]))
    age_labels = dfr.loc[('White', slice(None)), :].index.get_level_values(level=1).tolist()

    # Plot

    ri_w, = ax.plot(
        age_inds, dfr.loc[('White', slice(None)), 'RI^{[y1,y2]}'].tolist(),
        marker='p', ms=ms, lw=lw, ls=ls,
        color=color_w, markerfacecolor=markerfacecolor_w, markeredgecolor=markeredgecolor_w, markeredgewidth=markeredgewidth,
        zorder=5)

    ri_b, = ax.plot(
        age_inds, dfr.loc[('Black', slice(None)), 'RI^{[y1,y2]}'].tolist(),
        marker='h', ms=ms, lw=lw, ls=ls,
        color=color_b, markerfacecolor=markerfacecolor_b, markeredgecolor=markeredgecolor_b, markeredgewidth=markeredgewidth,
        zorder=5)

    """
    # Random Model
    ri_rnd_w, = ax.plot(
        age_inds, dfng.loc[('White', slice(None)), ('RI^{[y1,y2]}_{rnd}', 'mean')].values,
        marker='*', ms=6, markerfacecolor=markerfacecolor_w, markeredgecolor=markeredgecolor_w, lw=0, linestyle='-', zorder=6)


    ri_rnd_w, = ax.plot(
        age_inds, dfng.loc[('Black', slice(None)), ('RI^{[y1,y2]}_{rnd}', 'mean')].values,
        marker='*', ms=6, markerfacecolor=markerfacecolor_b, markeredgecolor=markeredgecolor_b, lw=0, linestyle='-', zorder=6)

    ri_rnd_w_ci = ax.fill_between(
        age_inds, y1=dfng.loc[('White', slice(None)), ('RI^{[y1,y2]}_{rnd}', 'ci95-max')], y2=dfng.loc[('White', slice(None)), ('RI^{[y1,y2]}_{rnd}', 'ci95-min')],
        color='lightpink', edgecolor='lightgray', lw=1)

    ri_rnd_w_ci = ax.fill_between(
        age_inds, y1=dfng.loc[('Black', slice(None)), ('RI^{[y1,y2]}_{rnd}', 'ci95-max')], y2=dfng.loc[('Black', slice(None)), ('RI^{[y1,y2]}_{rnd}', 'ci95-min')],
        color='lightpink', edgecolor='lightgray', lw=1)
    """

    # Plot Cubic Fit
    # rc_m_cubic, = ax.plot(x_, y_rc_m_, color='#ff7f0e', ms=0, lw=2, zorder=3)
    # rc_f_cubic, = ax.plot(x_, y_rc_f_, color='#ff7f0e', ms=0, lw=2, zorder=3)

    # R^2
    # ax.text(x=0.97, y=0.03, s=r'$R^2={:.3f}$'.format(ri_c_model_R2), ha='right', va='bottom', transform=ax.transAxes)

    # Legend
    ax.legend(
        [ri_w, ri_b], [r'$RI^{[y_1,y_2],W}$', r'$RI^{[y_1,y_2],B}$'],
        loc='best', handletextpad=0.5, columnspacing=0, handlelength=2, ncol=1)


    ax.set_xticks(age_inds)
    ax.set_xticklabels(age_labels, rotation=90)
    ax.grid()
    #ax.set_xlim(-.6,len(age_inds)-0.4)

    # Save
    plt.tight_layout()
    wIMGfile = 'images/img-ri-age-race.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()
