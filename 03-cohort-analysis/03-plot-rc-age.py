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
            COUNT(*) as 'patient-coadmin'
        FROM (
            SELECT
                c.id_patient,
                c.age,
                COUNT(*) AS 'coadmin'
            FROM dw_coadministration c
            WHERE
                c.age IS NOT NULL
            GROUP BY c.id_patient, c.age
        ) as t
        GROUP BY t.age
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col='age')
    # Map age to age_group
    dfc['age_group'] = map_age_to_age_group(dfc.index)
    # Group by age_group
    dfc = dfc.groupby('age_group').agg({'patient-coadmin': 'sum'})

    # Concat Results
    dfr = pd.concat([dfp, dfc], axis='columns', sort='False').fillna(0)

    # Risk of CoAdministration (per age_group)
    dfr['RC^{[y1,y2]}'] = (dfr['patient-coadmin'] / dfr['patient'])

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
