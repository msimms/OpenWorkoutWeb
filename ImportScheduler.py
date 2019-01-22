# Copyright 2018 Michael J Simms
"""Schedules computationally expensive import tasks"""

import os
from bson.json_util import dumps
from ImportWorker import import_activity

class ImportScheduler(object):
    """Class for scheduling computationally expensive import tasks."""

    def __init__(self):
        super(ImportScheduler, self).__init__()

    def add_to_queue(self, username, user_id, uploaded_file_data, uploaded_file_name):
        """Adds the activity ID to the list of activities to be analyzed."""
        params = {}
        params['username'] = username
        params['user_id'] = user_id
        params['uploaded_file_data'] = uploaded_file_data
        params['uploaded_file_name'] = uploaded_file_name
        import_obj = import_activity.delay(dumps(params))
