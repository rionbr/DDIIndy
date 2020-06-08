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

    # Load data
    dfr = pd.read_csv('results/age.csv', index_col=['age_group'])
    print(dfr)

    #
    # Curve Fitting
    #
    y_rc = dfr['RC^{[y1,y2]}'].values
    x = np.arange(len(y_rc))
    x_ = np.linspace(x[0], x[-1], len(x) * 10)

    # RC Cubic Model
    Xc = sm.add_constant(np.column_stack([x**3, x**2, x]))
    rc_c_model = sm.OLS(y_rc, Xc)
    rc_c_model_result = rc_c_model.fit()
    # print(rc_c_model_result.summary())
    Xc_ = sm.add_constant(np.column_stack([x_**3, x_**2, x_]))
    y_rc_ = np.dot(Xc_, rc_c_model_result.params)
    rc_c_model_R2 = rc_c_model_result.rsquared_adj

    #
    # Plot
    #
    fig, ax = plt.subplots(figsize=(4.3, 3), nrows=1, ncols=1)
    ax.set_title(r'$RC^{[y_1,y_2]}$')
    #
    age_inds = np.arange(0, len(dfr))
    age_labels = dfr.index.tolist()

    # Plot
    rc, = ax.plot(age_inds, dfr['RC^{[y1,y2]}'].tolist(), marker='o', ms=6, lw=0, markerfacecolor='#ffbb78', markeredgecolor='#ff7f0e', zorder=5)

    # Plot Cubic Fit
    rc_f_cubic, = ax.plot(x_, y_rc_, color='#ff7f0e', ms=0, lw=2, zorder=3)

    # R^2
    ax.text(x=0.97, y=0.03, s=r'$R^2={:.3f}$'.format(rc_c_model_R2), ha='right', va='bottom', transform=ax.transAxes)

    #Legend
    ax.legend([rc], [r'$RC^{[y_1,y_2]}$'], loc=2, handletextpad=0.5, columnspacing=0, handlelength=2, ncol=1)

    ax.set_xticks(age_inds)
    ax.set_xticklabels(age_labels, rotation=90)
    ax.grid()
    #ax.set_xlim(-.6,len(age_inds)-0.4)

    # Save
    plt.tight_layout()
    wIMGfile = 'images/img-rc-age.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()
