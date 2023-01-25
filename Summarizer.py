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
"""Summerizes a user's activities. Used for determining recent personal records."""

import time
import FtpCalculator
import HeartRateCalculator
import Keys

class Summarizer(object):
    """Class for summarizing a user's activities."""

    def __init__(self):
        self.bests = {} # Best ever times (best mile, best 20 minute power, etc.), dictionary of key/value pairs
        self.annual_bests = {} # Best times for each year  (best mile, best 20 minute power, etc.), dictionary of dictionaries of key/value pairs
        self.summaries = {} # Summary data (total distance, etc.)

        self.ftp_calc = FtpCalculator.FtpCalculator()
        self.hr_calc = HeartRateCalculator.HeartRateCalculator()

    def normalize_activity_type(self, activity_type):
        """Allows us to group activities such as running and virtual running together, for example."""
        if activity_type in Keys.RUNNING_ACTIVITIES:
            return Keys.TYPE_RUNNING_KEY
        if activity_type in Keys.CYCLING_ACTIVITIES:
            return Keys.TYPE_CYCLING_KEY
        return activity_type

    def get_record_dictionary(self, activity_type):
        """Returns the record dictionary that corresponds to the given activity type."""
        norm_activity_type = self.normalize_activity_type(activity_type)
        if norm_activity_type in self.bests:
            return self.bests[norm_activity_type]
        return {}

    def set_record_dictionary(self, activity_type, new_bests):
        """Sets the record dictionary that corresponds to the given activity type."""
        norm_activity_type = self.normalize_activity_type(activity_type)
        self.bests[norm_activity_type] = new_bests

    def get_annual_record_dictionary(self, activity_type, year):
        """Returns the annual record dictionary that corresponds to the given activity type and year."""

        # Top level dictionary is the year.
        if year not in self.annual_bests:
            self.annual_bests[year] = {}
        year_dictionary = self.annual_bests[year]

        # Next dictionary is the activity type and it's records.
        norm_activity_type = self.normalize_activity_type(activity_type)
        if norm_activity_type in year_dictionary:
            record_dictionary = year_dictionary[norm_activity_type]
        else:
            record_dictionary = {}
            year_dictionary[norm_activity_type] = record_dictionary
            self.annual_bests[year] = year_dictionary
        return record_dictionary

    def set_annual_record_dictionary(self, activity_type, year, record_dictionary):
        """Set the annual record dictionary that corresponds to the given activity type and year."""

        # Top level dictionary is the year.
        if year not in self.annual_bests:
            self.annual_bests[year] = {}
        year_dictionary = self.annual_bests[year]

        # Next dictionary is the activity type and it's records.
        norm_activity_type = self.normalize_activity_type(activity_type)
        year_dictionary[norm_activity_type] = record_dictionary
        self.annual_bests[year] = year_dictionary

    def get_annual_record_years(self):
        """Returns the years for which we have records."""
        return self.annual_bests.keys()

    def get_summary_dictionary(self, activity_type):
        """Returns the record dictionary that corresponds to the given activity type."""
        norm_activity_type = self.normalize_activity_type(activity_type)
        if norm_activity_type not in self.summaries:
            self.summaries[norm_activity_type] = {}
        return self.summaries[norm_activity_type]

    def set_summary_dictionary(self, activity_type, summary_dictionary):
        """Returns the record dictionary that corresponds to the given activity type."""
        norm_activity_type = self.normalize_activity_type(activity_type)
        self.summaries[norm_activity_type] = summary_dictionary

    def get_best_time(self, activity_type, record_name):
        """Returns the time associated with the specified record, or None if not found."""
        record_set = self.get_record_dictionary(activity_type)
        if record_name in record_set:
            time, _ = record_set[record_name]
            return time
        return None

    def get_best_time_for_year(self, activity_type, record_name, year):
        """Returns the time associated with the specified record, or None if not found."""
        record_set = self.get_annual_record_dictionary(activity_type, year)
        if record_name in record_set:
            time, _ = record_set[record_name]
            return time
        return None

    def get_best_time_from_record_set(self, record_set, record_name):
        """Returns the time associated with the specified record, or None if not found."""
        if record_name in record_set:
            time, _ = record_set[record_name]
            return time
        return None

    @staticmethod
    def is_better(key, lhs, rhs):
        if key in Keys.TIME_KEYS: # Lower is better
            return lhs < rhs
        elif key in Keys.SPEED_KEYS or key in Keys.POWER_KEYS or key in Keys.DISTANCE_KEYS: # Higher is better
            return lhs > rhs
        elif key == Keys.INTENSITY_SCORE:
            return lhs > rhs
        return False

    def add_activity_datum(self, activity_id, activity_type, start_time, summary_data_key, summary_data_value):
        """Submits one item of an activity's metadata for summary analysis."""

        # Ignore these ones.
        if summary_data_key in Keys.UNSUMMARIZABLE_KEYS:
            return

        # Get the record set that corresponds with the activity type.
        record_set = self.get_record_dictionary(activity_type)

        # Find the old record.
        old_value = self.get_best_time_from_record_set(record_set, summary_data_key)

        # If the old record is not set or this is better, then update.
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            record_set[summary_data_key] = [ summary_data_value, activity_id ]

        # Update the record set.
        self.set_record_dictionary(activity_type, record_set)

        #
        # Update annual records.
        #

        # In what year was this activity?
        ts = time.gmtime(start_time)

        # Get the record set that corresponds with the activity type.
        annual_record_set = self.get_annual_record_dictionary(activity_type, ts.tm_year)

        # Find the old record.
        old_value = self.get_best_time_from_record_set(annual_record_set, summary_data_key)

        # If the old record is not set or this is better, then update.
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            annual_record_set[summary_data_key] = [ summary_data_value, activity_id ]

        # Update the record set.
        self.set_annual_record_dictionary(activity_type, ts.tm_year, annual_record_set)

        #
        # Update summary data.
        #

        # Get the record set that corresponds with the activity type.
        summary_record_set = self.get_summary_dictionary(activity_type)

        # Update the distance and activity totals.
        if summary_data_key == Keys.LONGEST_DISTANCE:

            # Update total distance.
            if Keys.TOTAL_DISTANCE in summary_record_set:
                summary_record_set[Keys.TOTAL_DISTANCE] = summary_record_set[Keys.TOTAL_DISTANCE] + summary_data_value
            else:
                summary_record_set[Keys.TOTAL_DISTANCE] = summary_data_value

            # Update activity count.
            if Keys.TOTAL_ACTIVITIES in summary_record_set:
                summary_record_set[Keys.TOTAL_ACTIVITIES] = summary_record_set[Keys.TOTAL_ACTIVITIES] + 1
            else:
                summary_record_set[Keys.TOTAL_ACTIVITIES] = 1

        # Update the distance and activity totals.
        elif summary_data_key == Keys.APP_DURATION_KEY:

            # Update total duration.
            if Keys.APP_DURATION_KEY in summary_record_set:
                summary_record_set[Keys.TOTAL_DURATION] = summary_record_set[Keys.TOTAL_DURATION] + summary_data_value
            else:
                summary_record_set[Keys.TOTAL_DURATION] = summary_data_value

        # Update the intensity score summary.
        elif summary_data_key == Keys.INTENSITY_SCORE:

            if Keys.TOTAL_INTENSITY_SCORE in summary_record_set:
                summary_record_set[Keys.TOTAL_INTENSITY_SCORE] = summary_record_set[Keys.TOTAL_INTENSITY_SCORE] + summary_data_value
            else:
                summary_record_set[Keys.TOTAL_INTENSITY_SCORE] = summary_data_value

        # Update the record set.
        self.set_summary_dictionary(activity_type, summary_record_set)

    def add_activity_data(self, activity_id, activity_type, start_time, summary_data):
        """Submits an activity's metadata for summary analysis."""
        for key in summary_data:
            self.add_activity_datum(activity_id, activity_type, start_time, key, summary_data[key])
        self.ftp_calc.add_activity_data(activity_type, start_time, summary_data)
        self.hr_calc.add_activity_data(start_time, summary_data)
