# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Plot regressions on coadmin and interactions
#
#
import configparser
import numpy as np
import pandas as pd
import swifter
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists
import statsmodels.api as sm
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def calc_color_per_gender_and_age(row, scmap_female, scmap_male, scmap_gray):
    age = row.get('age', 0)
    gender = row.get('gender', None)
    #
    if gender is None:
        return scmap_gray.to_rgba(age)
    else:
        if gender == 'Male':
            return scmap_male.to_rgba(age)
        elif gender == 'Female':
            return scmap_female.to_rgba(age)


if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    sqlm = """
        SELECT
            p.id_patient,
            COUNT(DISTINCT md.id_drug) AS 'drugs',
            GROUP_CONCAT(DISTINCT p.gender) AS 'gender',
            GROUP_CONCAT(DISTINCT p.age_today) AS 'age'
        FROM patient p
            RIGHT JOIN medication m ON p.id_patient = m.id_patient
            RIGHT JOIN medication_drug md ON m.id_medication = md.id_medication
        GROUP BY p.id_patient
    """
    dfm = pd.read_sql(sqlm, con=engine, index_col='id_patient')
    dfm.fillna('None')

    sqlc = """
        SELECT
            p.id_patient,
            SUM(1) AS 'coadmin',
            SUM(CASE WHEN c.is_ddi = 1 THEN 1 ELSE 0 END) as 'inter'
        FROM patient p
            RIGHT JOIN coadministration c ON p.id_patient = c.id_patient
        GROUP BY p.id_patient
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='id_patient')

    # Concat
    df = pd.concat([dfm, dfc], axis='columns')

    # Fillna
    df[['coadmin', 'inter']] = df[['coadmin', 'inter']].fillna(0)
    # Dtypes
    df['age'] = pd.to_numeric(df['age'])

    # Init Values
    n = len(df)
    drugs = df['drugs'] + np.random.rand(n)
    coadmin = df['coadmin'] + np.random.rand(n)
    inter = df['inter'] + np.random.rand(n)

    norm = mpl.colors.Normalize(vmin=0, vmax=80)
    darkred = '#d62728'
    lightred = '#fae9e9'
    darkblue = '#1f77b4'
    lightblue = '#e8f1f7'

    cmap_female = LinearSegmentedColormap.from_list('female', [lightred, darkred])
    cmap_male = LinearSegmentedColormap.from_list('male', [lightblue, darkblue])
    cmap_gray = LinearSegmentedColormap.from_list('gray', ['#f2f2f2', '#7f7f7f'])
    scmap_female = ScalarMappable(norm=norm, cmap=cmap_female)
    scmap_male = ScalarMappable(norm=norm, cmap=cmap_male)
    scmap_gray = ScalarMappable(norm=norm, cmap=cmap_gray)

    cmap_female.set_over(darkred)
    cmap_male.set_over(darkblue)

    scmap_male.set_array(df['age'].values)
    scmap_female.set_array(df['age'].values)
    scmap_gray.set_array(df['age'].values)

    #
    df['color'] = df.swifter.apply(calc_color_per_gender_and_age, axis='columns', args=(scmap_female, scmap_male, scmap_gray, ))
    color = df['color']

    # Plot
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(8.5, 3.0))
    axin1 = inset_axes(ax1, width='50%', height='20%', loc='upper left')
    axin2 = inset_axes(ax2, width='50%', height='20%', loc='upper left')
    axin3 = inset_axes(ax3, width='50%', height='20%', loc='upper left')

    mpl.rcParams['mathtext.fontset'] = 'cm'
    mpl.rcParams['mathtext.rm'] = 'serif'
    mpl.rcParams['axes.titlesize'] = 'medium'
    mpl.rcParams['axes.labelsize'] = 'small'
    mpl.rcParams['xtick.labelsize'] = 'small'
    mpl.rcParams['ytick.labelsize'] = 'small'

    lw = 1
    s = 8
    sc1 = ax1.scatter(drugs, coadmin, s=s, c=color, alpha=1, marker='.', linewidths=0.4, edgecolors='None', rasterized=True)
    sc2 = ax2.scatter(drugs, inter, s=s, c=color, alpha=1, marker='.', linewidths=0.4, edgecolors='None', rasterized=True)
    sc3 = ax3.scatter(inter, coadmin, s=s, c=color, alpha=1, marker='.', linewidths=0.4, edgecolors='None', rasterized=True)

    ax1.set_title(r'Coadmin. from drugs')  # ($\Psi^{u}$ from $\nu^{u}$)')
    ax2.set_title(r'Interactions from drugs')  # ($\Phi^{u}$ from $\nu^{u}$)')
    ax3.set_title(r'Interactions from coadmin.')  # ($\Phi^{u}$ from $\Psi^{u}$)')

    ax1.set_xlabel(r'Drugs ($\nu^{u}$)')
    ax1.set_ylabel(r'Coadmin. ($\Psi^{u}$)')
    ax2.set_xlabel(r'Drugs ($\nu^{u}$)')
    ax2.set_ylabel(r'Interactions ($\Phi^{u}$)')
    ax3.set_ylabel(r'Coadmin. ($\Phi^{u}$)')
    ax3.set_xlabel(r'Interactions ($\Psi^{u}$)')

    axin1.set_xlabel('Complexity', fontsize='x-small')
    axin1.set_ylabel(r'$R^2$', fontsize='x-small')
    axin2.set_xlabel('Complexity', fontsize='x-small')
    axin2.set_ylabel(r'$R^2$', fontsize='x-small')
    axin3.set_xlabel('Complexity', fontsize='x-small')
    axin3.set_ylabel(r'$R^2$', fontsize='x-small')

    axin1.tick_params(axis='both', which='major', labelsize='x-small')
    axin2.tick_params(axis='both', which='major', labelsize='x-small')
    axin3.tick_params(axis='both', which='major', labelsize='x-small')

    ax1.grid()
    ax2.grid()
    ax3.grid()

    axin1.grid()
    axin2.grid()
    axin3.grid()

    #
    # Regressions
    #
    exponent_max = 4
    regression_color = {1: '#7f7f7f', 2: '#ff7f0e', 3: '#7f7f7f', 4: '#7f7f7f'}
    # OLS (drugs,coadmin)
    r = []
    x_ = np.linspace(1, drugs.max(), 100)
    for exponent in range(1, exponent_max + 1):
        xl = []
        xl_ = []
        for i in range(1, exponent + 1):
            xl.append(drugs**i)
            xl_.append(x_**i)
        xl = sm.add_constant(np.column_stack(xl))
        xl_ = sm.add_constant(np.column_stack(xl_))
        ols = sm.OLS(coadmin, xl).fit()
        y_ = np.dot(xl_, ols.params)
        #
        if exponent == 2:
            ax1.plot(x_, y_, color=regression_color[exponent], lw=lw, zorder=5)
            ylimmin, ylimmax = ax1.get_ylim()
            yper = 0.1 * (ylimmax - ylimmin)
            ax1.annotate(
                '{:.2f}'.format(ols.rsquared), xy=(x_[-15], y_[-15]), xytext=(x_[-12], y_[-15] - yper),
                fontsize='x-small', ha='left', va='top',
                arrowprops=dict(arrowstyle="->", connectionstyle='arc3,rad=-0.30', facecolor='gray', edgecolor='gray', lw=1),
                zorder=10)
        r.append(('coadmin', 'drug', exponent, ols.rsquared))
    #
    dfr = pd.DataFrame(r, columns=['x', 'y', 'exp', 'r2'])
    x, y = dfr['exp'].values, dfr['r2'].values
    axin1.scatter(x, y, c=list(regression_color.values()), s=10, marker='o', zorder=5)
    axin1.plot(x, y, color='#7f7f7f', marker='o', lw=lw, ms=0, zorder=3)
    axin1.yaxis.set_label_position('right')
    axin1.yaxis.tick_right()
    axin1.set_xticks(dfr['exp'])

    #OLS (drugs, interactions)
    r = []
    x_ = np.linspace(1, drugs.max(), 100)
    for exponent in range(1, exponent_max + 1):
        xl = []
        xl_ = []
        for i in range(1, exponent + 1):
            xl.append(drugs**i)
            xl_.append(x_**i)
        xl = sm.add_constant(np.column_stack(xl))
        xl_ = sm.add_constant(np.column_stack(xl_))
        ols = sm.OLS(inter, xl).fit()
        y_ = np.dot(xl_, ols.params)
        #
        if exponent == 2:
            ax2.plot(x_, y_, color=regression_color[exponent], lw=lw, zorder=5)
            ylimmin, ylimmax = ax2.get_ylim()
            yper = 0.1 * (ylimmax - ylimmin)
            ax2.annotate(
                '{:.2f}'.format(ols.rsquared), xy=(x_[-15], y_[-15]), xytext=(x_[-12], y_[-15] - yper),
                fontsize='x-small', ha='left', va='top',
                arrowprops=dict(arrowstyle="->", connectionstyle='arc3,rad=-0.30', facecolor='gray', edgecolor='gray', lw=1),
                zorder=10)
        r.append(('inter', 'drugs', exponent, ols.rsquared))
    #
    dfr = pd.DataFrame(r, columns=['x', 'y', 'exp', 'r2'])
    x, y = dfr['exp'].values, dfr['r2'].values
    axin2.scatter(x, y, c=list(regression_color.values()), s=10, marker='o', zorder=5)
    axin2.plot(x, y, color='#7f7f7f', marker='o', lw=lw, ms=0, zorder=3)
    axin2.yaxis.set_label_position('right')
    axin2.yaxis.tick_right()
    axin2.set_xticks(dfr['exp'])

    #OLS (coadmin, interaction)
    r = []
    x_ = np.linspace(1, inter.max(), 100)
    for exponent in range(1, exponent_max + 1):
        xl = []
        xl_ = []
        for i in range(1, exponent + 1):
            xl.append(inter**i)
            xl_.append(x_**i)
        xl = sm.add_constant(np.column_stack(xl))
        xl_ = sm.add_constant(np.column_stack(xl_))
        ols = sm.OLS(coadmin, xl).fit()
        y_ = np.dot(xl_, ols.params)
        #
        if exponent == 2:
            ax3.plot(x_, y_, color=regression_color[exponent], lw=lw, zorder=5)
            ylimmin, ylimmax = ax3.get_ylim()
            yper = 0.1 * (ylimmax - ylimmin)
            ax3.annotate(
                '{:.2f}'.format(ols.rsquared), xy=(x_[-15], y_[-15]), xytext=(x_[-12], y_[-15] - yper),
                fontsize='x-small', ha='left', va='top',
                arrowprops=dict(arrowstyle="->", connectionstyle='arc3,rad=-0.30', facecolor='gray', edgecolor='gray', lw=1),
                zorder=10)
        r.append(('inter', 'coadmin', exponent, ols.rsquared))
    #
    dfr = pd.DataFrame(r, columns=['x', 'y', 'exp', 'r2'])
    x, y = dfr['exp'].values, dfr['r2'].values
    axin3.scatter(x, y, c=list(regression_color.values()), s=10, marker='o', zorder=5)
    axin3.plot(x, y, color='#7f7f7f', marker='o', lw=lw, ms=0, zorder=3)
    axin3.yaxis.set_label_position('right')
    axin3.yaxis.tick_right()
    axin3.set_xticks(dfr['exp'])


    # Colorbars
    cax_female = fig.add_axes([0.61, 0.09, .15, .02])  # left, bottom, width, height
    cax_male = fig.add_axes([0.28, 0.09, .15, .02])

    N = 64
    boundaries = np.linspace(0, 90, N)
    ticks = [0, 20, 40, 60, 80]
    extendfrac = 0.075
    cb_female = mpl.colorbar.ColorbarBase(
        cax_female, cmap=cmap_female, norm=norm, boundaries=boundaries,
        extend='max', extendfrac=extendfrac, ticks=ticks, spacing='proportional', orientation='horizontal')
    cb_male = mpl.colorbar.ColorbarBase(
        cax_male, cmap=cmap_male, norm=norm, boundaries=boundaries,
        extend='max', extendfrac=extendfrac, ticks=ticks, spacing='proportional', orientation='horizontal')
    cb_female.ax.set_title(r'Male $y$', fontsize='small')
    cb_male.ax.set_title(r'Female $y$', fontsize='small')
    cb_female.ax.tick_params(labelsize='small')
    cb_male.ax.tick_params(labelsize='small')

    # Export
    plt.subplots_adjust(left=0.10, bottom=0.30, right=0.97, top=0.90, wspace=0.38, hspace=0.00)
    plt.savefig('images/img-drug-coadmin-inter-regre.pdf', dpi=300) #, frameon=True, bbox_inches='tight', pad_inches=0.0)
    plt.close()
