# Copyright 2019 Michael J Simms
"""Estimates body mass index."""

import time
import Keys

class BmiCalculator(object):
    """Estimates body mass index"""

    def __init__(self):
        super(BmiCalculator, self).__init__()

    def estimate_bmi(self, weight_kg, height_m):
        # bmi = kg / m2
        return weight_kg / (height_m * height_m)
