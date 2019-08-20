# Copyright 2019 Michael J Simms
"""Base class for heat map generation."""

class HeatMap(object):
    """Base class for heat map generation."""

    def __init__(self):
        self.map = {}
        self.max_value = 1
        super(HeatMap, self).__init__()

    def append(self, value):
        try:
            new_value = self.map[value] + 1
            self.map[value] = new_value
            if new_value > self.max_value:
                self.max_value = new_value
        except:
            self.map[value] = 1
