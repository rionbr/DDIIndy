# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Plot risk of interaction per age_group
#
#
import numpy as np
import pandas as pd
from utils import ensurePathExists, calc_confidence_interval
import statsmodels.api as sm
import matplotlib as mpl
mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['mathtext.rm'] = 'serif'
import matplotlib.pyplot as plt


if __name__ == '__main__':

    dfr = pd.read_csv('results/age.csv', index_col='age')
    print(dfr)

    #
    # Random Null Model
    #
    dfn = pd.read_csv('results/age_gender_race_zip_null_model.csv.gz')
    # Group by 'age_group' and 'run'
    dfn = dfn.groupby(['age_group', 'run']).agg({'patients': 'sum', 'patients_with_ddi': 'sum'})
    # Group by 'age_group' and compute confidence interval
    dfng = pd.DataFrame({
        'patients': dfn.groupby('age_group')['patients'].apply(calc_confidence_interval),
        'patients_with_ddi': dfn.groupby('age_group')['patients_with_ddi'].apply(calc_confidence_interval)
    }).unstack()
    # Compute RI (for mean, ci-max and ci-min)
    dfng[('RI^{y}_{rnd}', 'mean')] = (dfng[('patients_with_ddi', 'mean')] / dfng[('patients', 'mean')])
    dfng[('RI^{y}_{rnd}', 'ci95-max')] = (dfng[('patients_with_ddi', 'ci95-max')] / dfng[('patients', 'mean')])
    dfng[('RI^{y}_{rnd}', 'ci95-min')] = (dfng[('patients_with_ddi', 'ci95-min')] / dfng[('patients', 'mean')])

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

    # Random Model
    ri_rnd, = ax.plot(age_inds, dfn['RI^{y}_{rnd}'].values, marker='*', ms=6, markerfacecolor='#ff9896', markeredgecolor='#d62728', lw=0, linestyle='-', zorder=6)
    ri_rnd_ci = ax.fill_between(age_inds, y1=dfn['RI^{y}_{rnd}-ci_min'].values, y2=dfn['RI^{y}_{rnd}-ci_max'].values, color='lightpink', edgecolor='lightgray', lw=1)

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
