# coding=utf-8
# Author: Rion B Correia
# Date: May 20, 2020
#
# Description: Plots the colorbar used in the network composite
#
import matplotlib as mpl
from matplotlib import pyplot as plt
import numpy as np


if __name__ == '__main__':

    # Init
    N = 64
    boundaries = np.linspace(0.6, 5.4, N)
    ticks = [1, 2, 3, 4, 5]
    norm = mpl.colors.Normalize(vmin=1, vmax=5)
    extendfrac = 0.075

    darkred = '#d62728'
    lightred = '#fae9e9'
    darkblue = '#1f77b4'
    lightblue = '#e8f1f7'
    gray = '#7f7f7f'

    #
    # Plot ColorBar
    #
    fig = plt.figure(figsize=(2, 2))
    plt.rc('font', size=12, family='Helvetica', weight='regular')
    plt.rc('legend', fontsize=10, numpoints=1, labelspacing=0.3, frameon=False)
    plt.rc('axes', edgecolor='d8d9d8', linewidth=1)

    ax_female = fig.add_axes([0.15, 0.05, 0.11, 0.9])
    ax_male = fig.add_axes([0.6, 0.05, 0.11, 0.9])

    cmap_female = mpl.colors.LinearSegmentedColormap.from_list('female', colors=[lightred, darkred], N=N)
    cmap_male = mpl.colors.LinearSegmentedColormap.from_list('male', colors=[lightblue, darkblue], N=N)

    cmap_female.set_under(gray)
    cmap_male.set_under(gray)
    #
    cmap_female.set_over(darkred)
    cmap_male.set_over(darkblue)

    cb_female = mpl.colorbar.ColorbarBase(
        ax_female, cmap=cmap_female, norm=norm, boundaries=boundaries,
        extend='max', extendfrac=extendfrac, ticks=ticks, spacing='proportional', orientation='vertical')
    cb_male = mpl.colorbar.ColorbarBase(
        ax_male, cmap=cmap_male, norm=norm, boundaries=boundaries,
        extend='max', extendfrac=extendfrac, ticks=ticks, spacing='proportional', orientation='vertical')

    cb_female.solids.set_rasterized(False)
    cb_female.solids.set_edgecolor("face")
    cb_male.solids.set_rasterized(False)
    cb_male.solids.set_edgecolor("face")
    #
    # Save Colorbar
    #
    plt.savefig('images/img-colorbar-graph.pdf', dpi=300, transparent=True)
    plt.close()
