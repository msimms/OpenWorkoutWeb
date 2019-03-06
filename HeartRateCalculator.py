# Copyright 2019 Michael J Simms
"""Estimates the user's maximum heart rate and heart rate zones based on activity summary data."""

import inspect
import os
import sys
import time
import Keys

# Locate and load the statistics module (the functions we're using in are made obsolete in Python 3, but we want to work in Python 2, also)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import statistics

class HeartRateCalculator(object):
    """Estimates maximum heart rate and calculates heart rate training zones"""

    def __init__(self):
        self.rates = []
        self.cutoff_time = time.time() - ((365.25 / 2.0) * 24.0 * 60.0 * 60.0)
        super(HeartRateCalculator, self).__init__()

    def estimate_max_hr(self, age_in_years):
        """To be called after adding data with 'add_activity_data', estimates the user's maximum heart rate."""
        if len(self.rates) > 0:
            return statistics.mean(self.rates)
        return 207.0 - (0.7 * age_in_years) # Source: Gellish, 2007

    def training_zones(self, max_hr):
        """Returns the heart rate training zones as a function of estimated maximum heart rate."""
        zones = []
        zones.append(max_hr * 0.60)
        zones.append(max_hr * 0.70)
        zones.append(max_hr * 0.80)
        zones.append(max_hr * 0.90)
        zones.append(max_hr)
        return zones

    def add_activity_data(self, activity_type, start_time, summary_data):
        """Looks for data that will help us determine the user's maximum heart rate."""

        # Not interested in activities older than six months.
        if start_time < self.cutoff_time:
            return

        if Keys.MAX_HEART_RATE in summary_data:
            self.rates.append(summary_data[Keys.MAX_HEART_RATE])
