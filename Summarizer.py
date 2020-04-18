# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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
"""Summerizes a user's activities."""

import time
import FtpCalculator
import HeartRateCalculator
import Keys
import Units

class Summarizer(object):
    """Class for summarizing a user's activities."""

    def __init__(self):
        self.running_bests = {} # Best ever times (best mile, best 20 minute power, etc.)
        self.cycling_bests = {} # Best ever times (best mile, best 20 minute power, etc.)
        self.open_water_swimming_bests = {} # Best ever times (best mile, etc.)
        self.pool_swimming_bests = {} # Best ever times (best mile, etc.)

        self.annual_running_bests = {} # Best times for each year (best mile, best 20 minute power, etc.)
        self.annual_cycling_bests = {} # Best times for each year (best mile, best 20 minute power, etc.)
        self.annual_open_water_swimming_bests = {} # Best times for each year (best mile, etc.)
        self.annual_pool_swimming_bests = {} # Best times for each year (best mile, etc.)

        self.ftp_calc = FtpCalculator.FtpCalculator()
        self.hr_calc = HeartRateCalculator.HeartRateCalculator()

    def get_record_dictionary(self, activity_type):
        """Returns the record dictionary that corresponds to the given activity type."""
        if activity_type == Keys.TYPE_RUNNING_KEY:
            return self.running_bests
        elif activity_type == Keys.TYPE_CYCLING_KEY:
            return self.cycling_bests
        elif activity_type == Keys.TYPE_OPEN_WATER_SWIMMING_KEY:
            return self.open_water_swimming_bests
        elif activity_type == Keys.TYPE_POOL_SWIMMING_KEY:
            return self.pool_swimming_bests
        return {}

    def set_record_dictionary(self, activity_type, bests):
        """Sets the record dictionary that corresponds to the given activity type."""
        if activity_type == Keys.TYPE_RUNNING_KEY:
            self.running_bests = bests
        elif activity_type == Keys.TYPE_CYCLING_KEY:
            self.cycling_bests = bests
        elif activity_type == Keys.TYPE_OPEN_WATER_SWIMMING_KEY:
            self.open_water_swimming_bests = bests
        elif activity_type == Keys.TYPE_POOL_SWIMMING_KEY:
            self.pool_swimming_bests = bests

    def get_annual_record_dictionary(self, activity_type, year):
        """Returns the record dictionary that corresponds to the given activity type."""
        if activity_type == Keys.TYPE_RUNNING_KEY:
            if year not in self.annual_running_bests:
                self.annual_running_bests[year] = {}
            return self.annual_running_bests[year]
        elif activity_type == Keys.TYPE_CYCLING_KEY:
            if year not in self.annual_cycling_bests:
                self.annual_cycling_bests[year] = {}
            return self.annual_cycling_bests[year]
        elif activity_type == Keys.TYPE_OPEN_WATER_SWIMMING_KEY:
            if year not in self.annual_open_water_swimming_bests:
                self.annual_open_water_swimming_bests[year] = {}
            return self.annual_open_water_swimming_bests[year]
        elif activity_type == Keys.TYPE_POOL_SWIMMING_KEY:
            if year not in self.annual_pool_swimming_bests:
                self.annual_pool_swimming_bests[year] = {}
            return self.annual_pool_swimming_bests[year]
        return {}

    def get_annual_record_years(self, activity_type):
        """Returns the keys for the annual record dictionary that corresponds to the given activity type."""
        if activity_type == Keys.TYPE_RUNNING_KEY:
            return self.annual_running_bests.keys()
        elif activity_type == Keys.TYPE_CYCLING_KEY:
            return self.annual_cycling_bests.keys()
        elif activity_type == Keys.TYPE_OPEN_WATER_SWIMMING_KEY:
            return self.annual_open_water_swimming_bests.keys()
        elif activity_type == Keys.TYPE_POOL_SWIMMING_KEY:
            return self.annual_pool_swimming_bests.keys()
        return {}

    def get_best_time(self, activity_type, record_name):
        """Returns the time associated with the specified record, or None if not found."""
        record_set = self.get_record_dictionary(activity_type)
        if record_name in record_set:
            time, activity_id = record_set[record_name]
            return time
        return None

    def get_best_time_for_year(self, activity_type, record_name, year):
        """Returns the time associated with the specified record, or None if not found."""
        record_set = self.get_annual_record_dictionary(activity_type, year)
        if record_name in record_set:
            time, activity_id = record_set[record_name]
            return time
        return None

    def get_best_time_from_record_set(self, record_set, record_name):
        """Returns the time associated with the specified record, or None if not found."""
        if record_name in record_set:
            time, activity_id = record_set[record_name]
            return time
        return None

    @staticmethod
    def is_better(key, lhs, rhs):
        if key in Keys.TIME_KEYS: # Lower is better
            return lhs < rhs
        elif key in Keys.SPEED_KEYS or key in Keys.POWER_KEYS or key in Keys.DISTANCE_KEYS: # Higher is better
            return lhs > rhs
        return False

    def add_activity_datum(self, activity_id, activity_type, start_time, summary_data_key, summary_data_value):
        """Submits one item of an activity's metadata for summary analysis."""

        # Ignore these ones.
        if summary_data_key.find(Keys.CLUSTER) > 0:
            return
        if summary_data_key in Keys.UNSUMMARIZABLE_KEYS:
            return

        # Get the record set that corresponds with the activity type.
        record_set = self.get_record_dictionary(activity_type)

        # Find the old record.
        old_value = self.get_best_time_from_record_set(record_set, summary_data_key)

        # If the old record is not set or this is better, then update.
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            record_set[summary_data_key] = [ summary_data_value, activity_id ]

        # In what year was this activity?
        ts = time.gmtime(start_time)

        # Get the record set that corresponds with the activity type.
        record_set = self.get_annual_record_dictionary(activity_type, ts.tm_year)

        # Find the old record.
        old_value = self.get_best_time_from_record_set(record_set, summary_data_key)

        # If the old record is not set or this is better, then update.
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            record_set[summary_data_key] = [ summary_data_value, activity_id ]

    def add_activity_data(self, activity_id, activity_type, start_time, summary_data):
        """Submits an activity's metadata for summary analysis."""
        for key in summary_data:
            self.add_activity_datum(activity_id, activity_type, start_time, key, summary_data[key])
        self.ftp_calc.add_activity_data(activity_type, start_time, summary_data)
        self.hr_calc.add_activity_data(activity_type, start_time, summary_data)
