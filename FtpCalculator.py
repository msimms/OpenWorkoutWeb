# Copyright 2018 Michael J Simms
"""Estimates the user's Functional Threshold Power based on activity summary data."""

import time
import Keys

class FtpCalculator(object):
    """Data store abstraction"""

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

    def add_activity_data(self, activity_id, activity_type, start_time, summary_data):
        """Looks for data that will help us determine the user's FTP."""

        # Not interested in activities older than six months.
        if start_time < self.cutoff_time:
            return

        # Only intersted in cycling activities.
        if activity_type is not Keys.TYPE_CYCLING_KEY:
            return

        if Keys.BEST_20_MIN_POWER in summary_data:
            self.best_20min.append(summary_data[Keys.BEST_20_MIN_POWER])
        if Keys.BEST_1_HOUR_POWER in summary_data:
            self.best_1hr.append(summary_data[Keys.BEST_1_HOUR_POWER])
