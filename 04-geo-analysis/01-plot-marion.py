# coding=utf-8
# Author: Rion B Correia
# Date: April 17, 2020
#
# Description: Demographics
#
#
import configparser
import pandas as pd
import geopandas as gpd
import sqlalchemy
from sqlalchemy import event
from utils import add_own_encoders, ensurePathExists
import matplotlib as mpl
mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['mathtext.rm'] = 'serif'
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from shapely.geometry.polygon import Polygon


def plot_indianapolis_map(
        gdf=None,
        var=None,
        vmin=None,
        vmax=None,
        cmap=None,
        title='',
        legend_label='',
        legend_format=None,
        wIMGfile=None):
    # Plot
    fig, ax = plt.subplots(figsize=(6, 6), nrows=1, ncols=1)
    cax = fig.add_axes([0.15, 0.06, 0.70, 0.021])
    ax.set_title(title)

    # Patients
    """
    pp = gzip.plot(ax=ax, column='n-patients', cmap='jet', lw=0,
        legend=True,
        legend_kwds={
            'label':'Patients with at least one drug dispensation',
            'orientation':'horizontal',
            'format':FuncFormatter(lambda x, p: "{x:,.0f}".format(x=x))},
        cax=cax,
        zorder=3)
    """
    # Variable
    pp = gdf.plot(
        column=var,
        cmap=cmap,
        ax=ax,
        lw=0,
        legend=True,
        legend_kwds={
            'label': legend_label,
            'orientation': 'horizontal',
            'format': legend_format,
        },
        vmin=vmin,
        vmax=vmax,
        cax=cax,
        zorder=3)
    # ZCTA boundaries
    gdp1.boundary.plot(ax=ax, lw=1, edgecolor='#c7c7c7', zorder=4)
    # Counties
    gcounties.boundary.plot(ax=ax, lw=1.5, color='#d62728', zorder=8)
    # Highways
    ghighways.plot(ax=ax, lw=1, color='#7f7f7f', zorder=7)

    # Names
    def label_geometry(x):
        point = x['geometry'].representative_point()
        if zoom_polygon.contains(point):
            ax.text(x=point.x, y=point.y, s=x.get('ZCTA5CE10', ''), ha='center', fontsize='xx-small', zorder=12)
    gdp1.apply(label_geometry, axis=1)

    def xy_format(x, pos):
        return "{x:.0f}".format(x=(x / 1e4))

    ax.plot(*zoom_polygon.exterior.xy, color='green', lw=1)
    
    # Axis Label
    y_formatter = FuncFormatter(xy_format)
    x_formatter = FuncFormatter(xy_format)
    ax.xaxis.set_major_formatter(x_formatter)
    ax.yaxis.set_major_formatter(y_formatter)

    # Zoom in Marion County
    # minx, miny, maxx, maxy = gdp1.total_bounds
    minx, miny, maxx, maxy = zoom_polygon.bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # Save
    plt.subplots_adjust(left=0.10, right=0.95, bottom=0.14, top=0.93, wspace=0.0, hspace=0.0)
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()




if __name__ == '__main__':

    # DB
    cfg = configparser.ConfigParser()
    cfg.read('../config.ini')
    url = 'mysql+pymysql://%(user)s:%(pass)s@%(host)s/%(db)s?charset=utf8' % cfg['IU-RDC-MySQL']
    engine = sqlalchemy.create_engine(url, encoding='utf-8')
    event.listen(engine, "before_cursor_execute", add_own_encoders)

    # Zip to ZTCA CrossWalk
    dfzz = pd.read_excel('data/zip_to_zcta_2019.xlsx')
    dfzz = dfzz.loc[(dfzz['STATE'] == 'IN'), :]
    indiana_zcta = set(dfzz['ZCTA'].to_list())
    dict_zip_to_zcta = dfzz.set_index('ZIP_CODE')['ZCTA'].to_dict()

    # Polygon over Marion County
    minx, maxx, miny, maxy = (547000.0, 599000.0, 4380000.0, 4430000.0)
    zoom_polygon = Polygon([(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)])

    #
    # Load Cartographical data
    #
    # Counties
    gcountiesfile = 'zip://data/Census_Counties.zip!Census_County_TIGER00_IN.dbf'
    gcounties = gpd.read_file(gcountiesfile)
    counties = ['MARION', 'HAMILTON', 'MADISON', 'HANCOCK', 'SHELBY', 'JOHNSON', 'MORGAN', 'HENDRICKS', 'BOONE']
    gcounties = gcounties.loc[(gcounties['NAME_U'].isin(counties)), :]

    # Highways
    ghighwaysfile = 'zip://data/Interstates_Interstates_INDOT.zip!Interstates_INDOT_IN.dbf'
    ghighways = gpd.read_file(ghighwaysfile)
    routes = ['I-65', 'I-69', 'I-70', 'I-465', 'I-865']
    ghighways = ghighways.loc[(ghighways['ROUTE_NAME'].isin(routes)), :]

    # Lakes
    #glakesfiles = 'zip://data/Water_Bodies_Lakes_LocalRes.zip!Hydrography_LocalRes_WaterbodyDiscrete_NHD_IN.dbf'
    #glakes = gpd.read_file(glakesfiles)
    #glakes = glakes.loc[glakes['GNIS_Name'].isin(['Eagle Creek Reservoir', 'Geist Reservoir']), :]

    # Rivers
    #griversfile = 'zip://data/Water_Bodies_Rivers_Outstanding.zip!rivers_outstanding_nrc_in.dbf'
    #grivers = gpd.read_file(griversfile)

    # DP1 Profile
    dfdp1 = 'zip://data/Profile-ZCTA.zip!Profile-ZCTA.gdb'
    gdp1 = gpd.read_file(dfdp1)
    gdp1 = gdp1.loc[(gdp1['ZCTA5CE10'].isin(indiana_zcta)), :]
    gdp1 = gdp1.to_crs('EPSG:26916')
    gdp1.geometry = gdp1.geometry.simplify(tolerance=200)
    renames = {
        'DP0010001': 'population',
        'DP0010020': 'gender-male',
        'DP0010039': 'gender-female',
        'DP0080003': 'race-white',
        'DP0080004': 'race-black',
        'DP0110002': 'race-hispanic',
    }
    gdp1 = gdp1.rename(columns=renames)
    gdp1['gender-ratio'] = gdp1['gender-female'] / gdp1['gender-male']
    gdp1['race-white-norm'] = gdp1['race-white'] / gdp1['population']
    gdp1['race-black-norm'] = gdp1['race-black'] / gdp1['population']
    gdp1['race-hispanic-norm'] = gdp1['race-hispanic'] / gdp1['population']
    

    #
    # Plot
    #
    legend_format_thousand = FuncFormatter(lambda x, p: "{x:,.0f}".format(x=x))

    # Population
    plot_indianapolis_map(gdf=gdp1, var='population', title='Population', cmap='BuPu', legend_format=legend_format_thousand, wIMGfile='images/img-population.pdf')

    # Gender
    plot_indianapolis_map(gdf=gdp1, var='gender-ratio', title='Gender Ratio', cmap='seismic', vmin=0.8, vmax=1.2, wIMGfile='images/img-gender.pdf')

    # Race (White/Black/Hispanic)
    plot_indianapolis_map(gdf=gdp1, var='race-white-norm', title='Race (White)', cmap='Greys', vmin=0, vmax=1, wIMGfile='images/img-race-white.pdf')
    plot_indianapolis_map(gdf=gdp1, var='race-black-norm', title='Race (Black or African American)', cmap='Greys', vmin=0, vmax=1, wIMGfile='images/img-race-black.pdf')
    plot_indianapolis_map(gdf=gdp1, var='race-hispanic-norm', title='Race (Hispanic)', cmap='Greys', vmin=0, vmax=1, wIMGfile='images/img-race-hispanic.pdf')

    # IRS Income
    dfincome = pd.read_csv('data/17zpallagi.csv')
    dfincome = dfincome.rename(columns={'A00100': 'agi'})
    # Index
    dfincome = dfincome.loc[((dfincome['STATE'] == 'IN') & (dfincome['zipcode'] != 0)), ['STATE', 'zipcode', 'agi_stub', 'agi']]
    # Map ZIP to ZCTA
    dfincome['ZCTA'] = dfincome['zipcode'].apply(lambda x: dict_zip_to_zcta.get(x, None))
    # Group by ZCTA
    dfincomegroup = dfincome.groupby('ZCTA').agg({'agi': 'mean'}).reset_index()
    # Merge
    gtmp = gdp1.loc[:, ['ZCTA5CE10', 'population', 'geometry']].merge(dfincomegroup[['ZCTA', 'agi']], left_on='ZCTA5CE10', right_on='ZCTA')
    # Plot
    plot_indianapolis_map(gdf=gtmp, var='agi', title='Adjusted Gross Income', cmap='Oranges', vmin=0, vmax=None, legend_format=legend_format_thousand, wIMGfile='images/img-income.pdf')

    # Patients
    sqlg = """
        SELECT
            p.zip5,
            COUNT(*) AS 'patients'
        FROM patient p
        WHERE
            p.zip5 IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.zip5
    """
    dfp = pd.read_sql(sqlg, con=engine, index_col=None)
    # More than 1 dispensation
    #dfp = dfp.loc[dfp['patients'] > 5, :]
    # Maps ZIP to ZCTA
    dfp['ZCTA'] = dfp['zip5'].apply(lambda x: dict_zip_to_zcta.get(x, None))
    # Group by ZCTA
    dfp = dfp.groupby('ZCTA').agg({'patients': 'sum'}).reset_index()
    # Merge
    gtmp = gdp1.loc[:, ['ZCTA5CE10', 'population', 'geometry']].merge(dfp[['ZCTA', 'patients']], left_on='ZCTA5CE10', right_on='ZCTA')
    # Norm
    gtmp['patients-norm'] = gtmp['patients'] / gtmp['population']
    # Plot
    plot_indianapolis_map(gdf=gtmp, var='patients-norm', title='Patients (at least one dispensation)', cmap='Purples', vmin=0, vmax=1, wIMGfile='images/img-patients.pdf')

    # Drugs
    sqld = """
        SELECT
            p.zip5,
            COUNT(*) AS 'drugs'
        FROM medication_drug md
            JOIN medication m ON m.id_medication = md.id_medication
            JOIN patient p ON p.id_patient = m.id_patient
        WHERE
            p.zip5 IS NOT NULL
            AND
            p.id_patient IN (SELECT m.id_patient FROM medication m)
        GROUP BY p.zip5
    """
    dfd = pd.read_sql(sqld, con=engine, index_col=None)
    # Maps ZIP to ZCTA
    dfd['ZCTA'] = dfd['zip5'].apply(lambda x: dict_zip_to_zcta.get(x, None))
    # Group by ZCTA
    dfd = dfd.groupby('ZCTA').agg({'drugs': 'sum'}).reset_index()
    # Merge
    gtmp = gdp1.loc[:, ['ZCTA5CE10', 'population', 'geometry']].merge(dfd[['ZCTA', 'drugs']], left_on='ZCTA5CE10', right_on='ZCTA')
    # Norm
    gtmp['drugs-norm'] = gtmp['drugs'] / gtmp['population']
    # Plot
    plot_indianapolis_map(gdf=gtmp, var='drugs-norm', title='Drugs per capita', cmap='Purples', vmin=0, vmax=None, wIMGfile='images/img-drugs.pdf')

    # CoAdministration
    sqlc = """
        SELECT
            c.zip5,
            COUNT(*) AS 'coadmin'
        FROM dw_coadministration c
        WHERE
            c.zip5 IS NOT NULL
        GROUP BY c.zip5
    """
    dfc = pd.read_sql(sqlc, con=engine, index_col=None)
    # Maps ZIP to ZCTA
    dfc['ZCTA'] = dfc['zip5'].apply(lambda x: dict_zip_to_zcta.get(x, None))
    # Group by ZCTA
    dfc = dfc.groupby('ZCTA').agg({'coadmin': 'sum'}).reset_index()
    # Merge
    gtmp = gdp1.loc[:, ['ZCTA5CE10', 'population', 'geometry']].merge(dfc[['ZCTA', 'coadmin']], left_on='ZCTA5CE10', right_on='ZCTA')
    # Norm
    gtmp['coadmin-norm'] = gtmp['coadmin'] / gtmp['population']
    # Plots
    plot_indianapolis_map(gdf=gtmp, var='coadmin-norm', title='Co-administration per capita', cmap='Oranges', vmin=0, vmax=None, wIMGfile='images/img-coadmin.pdf')

    # Interaction
    sqli = """
        SELECT
            i.zip5,
            COUNT(*) AS 'inter'
        FROM dw_interaction i
        WHERE
            i.zip5 IS NOT NULL
        GROUP BY i.zip5
    """
    dfi = pd.read_sql(sqli, con=engine, index_col=None)
    # Maps ZIP to ZCTA
    dfi['ZCTA'] = dfi['zip5'].apply(lambda x: dict_zip_to_zcta.get(x, None))
    # Group by ZCTA
    dfi = dfi.groupby('ZCTA').agg({'inter': 'sum'}).reset_index()
    # Merge
    gtmp = gdp1.loc[:, ['ZCTA5CE10', 'population', 'geometry']].merge(dfi[['ZCTA', 'inter']], left_on='ZCTA5CE10', right_on='ZCTA')
    # Norm
    gtmp['inter-norm'] = gtmp['inter'] / gtmp['population']
    # Plot
    plot_indianapolis_map(gdf=gtmp, var='inter-norm', title='Interactions per capita', cmap='Reds', vmin=0, vmax=None, wIMGfile='images/img-inter.pdf')
