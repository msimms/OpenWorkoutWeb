# Copyright 2018 Michael J Simms
"""Schedules computationally expensive analysis tasks"""

import json
from bson.json_util import dumps
from ActivityAnalyzer import analyze_activity

class AnalysisScheduler(object):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self):
        self.enabled = True
        super(AnalysisScheduler, self).__init__()

    def add_to_queue(self, activity):
        """Adds the activity ID to the list of activities to be analyzed."""
        if not self.enabled:
            return
        analysis_obj = analyze_activity.delay(dumps(activity))
