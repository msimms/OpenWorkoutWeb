# Copyright 2019 Michael J Simms
"""Estimates the user's Functional Threshold Power based on activity summary data."""

import time
import Keys

class FtpCalculator(object):
    """Estimates functional threshold power and power training zones"""

    def __init__(self):
        self.best_20min = []
        self.best_1hr = []
        self.cutoff_time = time.time() - ((365.25 / 2.0) * 24.0 * 60.0 * 60.0)
        super(FtpCalculator, self).__init__()

    def estimate(self):
        """To be called after adding data with 'add_activity_data', estimates the user's FTP."""
        max_20min_adjusted = 0.0
        max_1hr = 0.0
        if len(self.best_20min) > 0:
            max_20min = max(self.best_20min)
            max_20min_adjusted = max_20min * 0.95
        if len(self.best_1hr) > 0:
            max_1hr = max(self.best_1hr)
        if max_1hr > max_20min_adjusted:
            return max_1hr
        return max_20min_adjusted

    def power_training_zones(self, ftp):
        """Returns the power training zones as a function of FTP."""
        # Zone 1 - Active Recovery - Less than 55% of FTP
        # Zone 2 - Endurance - 55% to 74% of FTP
        # Zone 3 - Tempo - 75% to 89% of FTP
        # Zone 4 - Lactate Threshold - 90% to 104% of FTP
        # Zone 5 - VO2 Max - 105% to 120% of FTP
        # Zone 6 - Anaerobic Capacity - More than 120% of FTP
        zones = []
        zones.append(ftp * 0.54)
        zones.append(ftp * 0.74)
        zones.append(ftp * 0.89)
        zones.append(ftp * 1.04)
        zones.append(ftp * 1.20)
        return zones

    def compute_power_zone_distribution(self, ftp, powers):
        """Takes the list of power readings and determines how many belong in each power zone, based on the user's FTP."""
        zones = self.power_training_zones(ftp)
        distribution = [0.0] * (len(zones) + 1)
        for datum in powers:
            value = float(datum.values()[0])
            index = 0
            found = False
            for zone_cutoff in zones:
                if value <= zone_cutoff:
                    distribution[index] = distribution[index] + 1
                    found = True
                    break
                index = index + 1
            if not found:
                distribution[index] = distribution[index] + 1
        return distribution

    def add_activity_data(self, activity_type, start_time, summary_data):
        """Looks for data that will help us determine the user's FTP. start_time is unix time (in seconds) and is used to compare against the cutoff time."""

        # Not interested in activities older than six months.
        if start_time < self.cutoff_time:
            return

        # Only intersted in cycling activities.
        if activity_type not in Keys.BIKE_BASED_ACTIVITIES:
            return

        if Keys.BEST_20_MIN_POWER in summary_data:
            self.best_20min.append(summary_data[Keys.BEST_20_MIN_POWER])
        if Keys.BEST_1_HOUR_POWER in summary_data:
            self.best_1hr.append(summary_data[Keys.BEST_1_HOUR_POWER])
