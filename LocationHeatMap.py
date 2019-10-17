# Copyright 2019 Michael J Simms
"""Heat map for location values."""

import HeatMap
from decimal import *

class LocationHeatMap(HeatMap.HeatMap):
    """Heat map for location values."""

    def __init__(self):
        HeatMap.HeatMap.__init__(self)
        getcontext().prec = 5

    def append(self, lat, lon):
        data = frozenset((Decimal(lat), Decimal(lon)))
        super(LocationHeatMap, self).append(data)
