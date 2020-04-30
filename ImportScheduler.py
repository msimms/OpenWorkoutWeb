# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Mike Simms
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
"""Schedules computationally expensive import tasks"""

import sys
import traceback
import Keys

from bson.json_util import dumps
from ImportWorker import import_activity

class ImportScheduler(object):
    """Class for scheduling computationally expensive import tasks."""

    def __init__(self):
        super(ImportScheduler, self).__init__()

    def add_to_queue(self, username, user_id, uploaded_file_data, uploaded_file_name, data_mgr):
        """Adds the activity ID to the list of activities to be analyzed."""
        try:
            params = {}
            params['username'] = username
            params['user_id'] = user_id
            params['uploaded_file_data'] = uploaded_file_data
            params['uploaded_file_name'] = uploaded_file_name
            import_task = import_activity.delay(dumps(params))
            if data_mgr is not None:
                data_mgr.create_deferred_task(user_id, Keys.IMPORT_TASK_KEY, import_task.task_id, uploaded_file_name)
        except:
            print(traceback.format_exc())
            print(sys.exc_info()[0])
