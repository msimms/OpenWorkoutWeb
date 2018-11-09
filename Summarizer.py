# Copyright 2018 Michael J Simms

import time
import StraenKeys
import Units


class Summarizer(object):
    """Class for summarizing a user's activities."""

    def __init__(self):
        self.running_bests = {} # Best ever times (best mile, best 20 minute power, etc.)
        self.cycling_bests = {} # Best ever times (best mile, best 20 minute power, etc.)
        self.swimming_bests = {} # Best ever times (best mile, etc.)

        self.annual_running_bests = {} # Best times for each year (best mile, best 20 minute power, etc.)
        self.annual_cycling_bests = {} # Best times for each year (best mile, best 20 minute power, etc.)
        self.annual_swimming_bests = {} # Best times for each year (best mile, etc.)

    def get_record_dictionary(self, activity_type):
        """Returns the record dictionary that corresponds to the given activity type."""
        if activity_type == StraenKeys.TYPE_RUNNING_KEY:
            return self.running_bests
        elif activity_type == StraenKeys.TYPE_CYCLING_KEY:
            return self.cycling_bests
        elif activity_type == StraenKeys.TYPE_SWIMMING_KEY:
            return self.swimming_bests
        return {}

    def get_annual_record_dictionary(self, activity_type, year):
        """Returns the record dictionary that corresponds to the given activity type."""
        if activity_type == StraenKeys.TYPE_RUNNING_KEY:
            if year not in self.annual_running_bests:
                self.annual_running_bests[year] = {}
            return self.annual_running_bests[year]
        elif activity_type == StraenKeys.TYPE_CYCLING_KEY:
            if year not in self.annual_cycling_bests:
                self.annual_cycling_bests[year] = {}
            return self.annual_cycling_bests[year]
        elif activity_type == StraenKeys.TYPE_SWIMMING_KEY:
            if year not in self.annual_swimming_bests:
                self.annual_swimming_bests[year] = {}
            return self.annual_swimming_bests[year]
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
        if key in [ StraenKeys.BEST_1K, StraenKeys.BEST_MILE, StraenKeys.BEST_10K, StraenKeys.BEST_15K, StraenKeys.BEST_HALF_MARATHON, StraenKeys.BEST_MARATHON, StraenKeys.BEST_METRIC_CENTURY, StraenKeys.BEST_CENTURY ]:
            return lhs < rhs
        elif key in [ StraenKeys.APP_AVG_SPEED_KEY, StraenKeys.BEST_5_SEC_POWER, StraenKeys.BEST_20_MIN_POWER, StraenKeys.BEST_1_HOUR_POWER ]:
            return rhs > lhs
        return False

    def add_activity_datum(self, activity_id, activity_type, start_time, summary_data_key, summary_data_value):
        """Submits one item of an activity's metadata for summary analysis."""

        # Ignore these ones.
        if summary_data_key.find(StraenKeys.CLUSTER) > 0:
            return

        # Get the record set that corresponds with the activity type.
        record_set = self.get_record_dictionary(activity_type)

        # Find the old record.
        old_value = self.get_best_time_from_record_set(record_set, summary_data_key)

        # If the old record is not set or this is better, then update.
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            record_set[summary_data_key] = { summary_data_value, activity_id }

        # In what year was this activity?
        ts = time.gmtime(start_time)

        # Get the record set that corresponds with the activity type.
        record_set = self.get_annual_record_dictionary(activity_type, ts.tm_year)

        # Find the old record.
        old_value = self.get_best_time_from_record_set(record_set, summary_data_key)

        # If the old record is not set or this is better, then update.
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            record_set[summary_data_key] = { summary_data_value, activity_id }

    def add_activity_data(self, activity_id, activity_type, start_time, summary_data):
        """Submits an activity's metadata for summary analysis."""
        for key in summary_data:
            self.add_activity_datum(activity_id, activity_type, start_time, key, summary_data[key])
