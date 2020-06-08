# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Plot risk of interaction per age_group
#
#
import numpy as np
import pandas as pd
from utils import ensurePathExists  # add_own_encoders #, map_age_to_age_group
import statsmodels.api as sm
import matplotlib as mpl
mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['mathtext.rm'] = 'serif'
import matplotlib.pyplot as plt


if __name__ == '__main__':

    # Load data
    dfr = pd.read_csv('results/age-gender.csv', index_col=['gender', 'age_group'])
    print(dfr)

    #
    # Random Null Model
    #
    """
    dfn = pd.read_csv('results/age_gender_race_zip_null_model.csv.gz')
    # Group by 'age_group' and 'run'
    dfn = dfn.groupby(['age_group', 'run']).agg({'patients': 'sum', 'patients_with_ddi': 'sum'})
    # Group by 'age_group' and compute confidence interval
    dfng = pd.DataFrame({
        'patients': dfn.groupby('age_group')['patients'].apply(calc_confidence_interval),
        'patients_with_ddi': dfn.groupby('age_group')['patients_with_ddi'].apply(calc_confidence_interval)
    }).unstack()
    # Compute RI (for mean, ci-max and ci-min)
    dfng[('RI^{[y1,y2]}_{rnd}', 'mean')] = (dfng[('patients_with_ddi', 'mean')] / dfng[('patients', 'mean')])
    dfng[('RI^{[y1,y2]}_{rnd}', 'ci95-max')] = (dfng[('patients_with_ddi', 'ci95-max')] / dfng[('patients', 'mean')])
    dfng[('RI^{[y1,y2]}_{rnd}', 'ci95-min')] = (dfng[('patients_with_ddi', 'ci95-min')] / dfng[('patients', 'mean')])
    """

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
    ax.set_title(r'$RI^{[y_1,y_2],g}$')
    #
    ms = 7
    lw = 1.5
    ls = '-.'
    markerfacecolor_f = '#f7b6d2'
    markerfacecolor_m = '#aec7e8'
    markeredgecolor_f = '#d62728'
    markeredgecolor_m = '#d62728'
    color_f = markeredgecolor_f
    color_m = markeredgecolor_m
    markeredgewidth = 1.5
    #
    age_inds = np.arange(0, len(dfr.loc[('Male', slice(None)), :]))
    age_labels = dfr.loc[('Male', slice(None)), :].index.get_level_values(level=1).tolist()

    # Plot
    ri_f, = ax.plot(
        age_inds, dfr.loc[('Female', slice(None)), 'RI^{[y1,y2]}'].tolist(),
        marker='D', ms=ms, lw=lw, ls=ls,
        color=color_f, markerfacecolor=markerfacecolor_f, markeredgecolor=markeredgecolor_f, markeredgewidth=markeredgewidth,
        zorder=5)
    ri_m, = ax.plot(
        age_inds, dfr.loc[('Male', slice(None)), 'RI^{[y1,y2]}'].tolist(),
        marker='s', ms=ms, lw=lw, ls=ls,
        color=color_m, markerfacecolor=markerfacecolor_m, markeredgecolor=markeredgecolor_m, markeredgewidth=markeredgewidth,
        zorder=5)

    # Plot Cubic Fit
    # rc_m_cubic, = ax.plot(x_, y_rc_m_, color='#ff7f0e', ms=0, lw=2, zorder=3)
    # rc_f_cubic, = ax.plot(x_, y_rc_f_, color='#ff7f0e', ms=0, lw=2, zorder=3)

    # R^2
    # ax.text(x=0.97, y=0.03, s=r'$R^2={:.3f}$'.format(ri_c_model_R2), ha='right', va='bottom', transform=ax.transAxes)

    # Legend
    ax.legend(
        [ri_f, ri_m], [r'$RI^{[y_1,y_2],F}$', r'$RI^{[y_1,y_2],M}$'],
        loc='best', handletextpad=0.5, columnspacing=0, handlelength=2, ncol=1)


    ax.set_xticks(age_inds)
    ax.set_xticklabels(age_labels, rotation=90)
    ax.grid()
    #ax.set_xlim(-.6,len(age_inds)-0.4)

    # Save
    plt.tight_layout()
    wIMGfile = 'images/img-ri-age-gender.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()
