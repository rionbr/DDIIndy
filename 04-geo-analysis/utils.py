# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: utility functions
#
#
import os
import numpy as np
import pandas as pd


def map_age_to_age_group(x):
    bins = list(range(0, 101, 5))
    labels = ['%02d-%02d' % (x, x1 - 1) for x, x1 in zip(bins[: -1], bins[1:])] + ['>99']
    #
    return pd.cut(x, bins=bins + [np.inf], include_lowest=True, right=False, labels=labels)


def add_own_encoders(conn, cursor, query, *args):
    cursor.connection.encoders[np.float64] = lambda value, encoders: float(value)
    cursor.connection.encoders[np.int64] = lambda value, encoders: int(value)


def ensurePathExists(path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
