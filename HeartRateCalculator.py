# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Michael J Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Estimates the user's maximum heart rate and heart rate zones based on activity summary data."""

import time
import Keys

class HeartRateCalculator(object):
    """Estimates maximum heart rate and calculates heart rate training zones"""

    def __init__(self):
        self.rates = []
        self.cutoff_time = time.time() - ((365.25 / 2.0) * 24.0 * 60.0 * 60.0)
        super(HeartRateCalculator, self).__init__()

    def estimate_max_hr(self, age_in_years):
        """To be called after adding data with 'add_activity_data', estimates the user's maximum heart rate."""
        """Uses actual data when available, falls back to a basic estimation."""
        if len(self.rates) > 0:
            return sum(self.rates) / len(self.rates)

        # Use the Oakland nonlinear formula to estimate based on age.
        return 192.0 - (0.007 * (age_in_years * age_in_years))

    def training_zones(self, max_hr, resting_hr, age_in_years):
        """Returns the heart rate training zones as a function of estimated maximum heart rate."""

        zones = []

        # If given resting and max heart rates, use the Karvonen formula for determining zones based on hr reserve.
        if resting_hr is not None and resting_hr > 1.0 and max_hr is not None and max_hr > 1.0:
            zones.append(((max_hr - resting_hr) * .60) + resting_hr)
            zones.append(((max_hr - resting_hr) * .70) + resting_hr)
            zones.append(((max_hr - resting_hr) * .80) + resting_hr)
            zones.append(((max_hr - resting_hr) * .90) + resting_hr)
            zones.append(max_hr)

        # Maximum heart rate, but no resting heart rate.
        elif max_hr > 1.0:
            zones.append(max_hr * 0.60)
            zones.append(max_hr * 0.70)
            zones.append(max_hr * 0.80)
            zones.append(max_hr * 0.90)
            zones.append(max_hr)

        # No heart rate information, estimate it based on age and then generate the zones.
        else:
            max_hr = self.estimate_max_hr(age_in_years)
            zones.append(max_hr * 0.60)
            zones.append(max_hr * 0.70)
            zones.append(max_hr * 0.80)
            zones.append(max_hr * 0.90)
            zones.append(max_hr)

        return zones

    def add_activity_data(self, start_time, summary_data):
        """Looks for data that will help us determine the user's maximum heart rate."""

        # Not interested in activities older than six months.
        if start_time < self.cutoff_time:
            return

        if Keys.MAX_HEART_RATE in summary_data:
            self.rates.append(summary_data[Keys.MAX_HEART_RATE])
