# Copyright 2019 Michael J Simms
"""Heat map for speed values."""

import HeatMap
from decimal import *

class SpeedHeatMap(HeatMap.HeatMap):
    """Class that generates a heat map for speed values."""

    def __init__(self):
        HeatMap.HeatMap.__init__(self)
        getcontext().prec = 1

    def append(self, value):
        data = Decimal(value)
        super(SpeedHeatMap, self).append(data)
