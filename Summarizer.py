# Copyright 2018 Michael J Simms

import StraenKeys
import Units


class Summarizer(object):
    """Class for summarizing a user's activities."""

    def __init__(self):
        self.bests = {} # Best times within the current activity (best mile, best 20 minute power, etc.)

    def get_best_time(self, record_name):
        """Returns the time associated with the specified record, or None if not found."""
        if record_name in self.bests:
            return self.bests[record_name]
        return None

    @staticmethod
    def is_better(key, lhs, rhs):
        if key in [ StraenKeys.BEST_1K, StraenKeys.BEST_MILE, StraenKeys.BEST_10K, StraenKeys.BEST_HALF_MARATHON, StraenKeys.BEST_MARATHON ]:
            return lhs < rhs
        elif key in [ StraenKeys.BEST_5_SEC_POWER, StraenKeys.BEST_20_MIN_POWER, StraenKeys.BEST_1_HOUR_POWER ]:
            return rhs > lhs
        return False

    def add_activity_datum(self, activity_id, summary_data_key, summary_data_value):
        old_value = self.get_best_time(summary_data_key)
        if old_value is None or Summarizer.is_better(summary_data_key, summary_data_value, old_value):
            self.bests[summary_data_key] = summary_data_value

    def add_activity_data(self, activity_id, summary_data):
        for key in summary_data:
            self.add_activity_datum(activity_id, key, summary_data[key])
