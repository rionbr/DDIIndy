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


if __name__ == '__main__':

    # Polygon over Marion County
    minx, maxx, miny, maxy = (547000.0, 599000.0, 4380000.0, 4430000.0)
    zoom_polygon = Polygon([(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)])

    #
    # Load Cartographical data
    #
    # Counties
    gcountiesfile = 'zip://data/Census_Counties.zip!Census_County_TIGER00_IN.dbf'
    gcounties = gpd.read_file(gcountiesfile)
    #counties = ['MARION', 'HAMILTON', 'MADISON', 'HANCOCK', 'SHELBY', 'JOHNSON', 'MORGAN', 'HENDRICKS', 'BOONE']
    #gcounties = gcounties.loc[(gcounties['NAME_U'].isin(counties)), :]

    # Highways
    ghighwaysfile = 'zip://data/Interstates_Interstates_INDOT.zip!Interstates_INDOT_IN.dbf'
    ghighways = gpd.read_file(ghighwaysfile)
    #routes = ['I-65', 'I-69', 'I-70', 'I-465', 'I-865']
    #ghighways = ghighways.loc[(ghighways['ROUTE_NAME'].isin(routes)), :]

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

    #
    # Plot
    #
    fig, ax = plt.subplots(figsize=(4.4, 6), nrows=1, ncols=1)
    #cax = fig.add_axes([0.15, 0.06, 0.70, 0.021])
    ax.set_title("Indiana")

    # Init
    gdf = gdp1
    title = 'Population'
    cmap = 'BuPu'

    # ZCTA
    gdp1.boundary.plot(ax=ax, lw=0.5, edgecolor='#c7c7c7', zorder=4)
    # Counties
    gcounties.boundary.plot(ax=ax, lw=0.75, color='#d62728', zorder=8)
    # Highways
    ghighways.plot(ax=ax, lw=0.8, color='#7f7f7f', zorder=7)

    def xy_format(x, pos):
        return "{x:.0f}".format(x=(x / 1e4))
    
    # Axis Label
    y_formatter = FuncFormatter(xy_format)
    x_formatter = FuncFormatter(xy_format)
    ax.xaxis.set_major_formatter(x_formatter)
    ax.yaxis.set_major_formatter(y_formatter)

    # Plot Zoom Polygon
    ax.plot(*zoom_polygon.exterior.xy, color='green', lw=1.5, zorder=10)

    # Zoom in Indiana
    minx, miny, maxx, maxy = gdp1.total_bounds
    #minx, miny, maxx, maxy = zoom_polygon.bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # Save
    plt.subplots_adjust(left=0.04, right=0.98, bottom=0.07, top=0.95, wspace=0.0, hspace=0.0)
    wIMGfile = 'images/img-indianapolis.pdf'
    ensurePathExists(wIMGfile)
    fig.savefig(wIMGfile)
    plt.close()
