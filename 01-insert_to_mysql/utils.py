# coding=utf-8
# Author: Rion B Correia
# Date: March 17, 2020
#
# Description: utility functions
#
#
import numpy as np


def add_own_encoders(conn, cursor, query, *args):
    cursor.connection.encoders[np.float64] = lambda value, encoders: float(value)
    cursor.connection.encoders[np.int64] = lambda value, encoders: int(value)
