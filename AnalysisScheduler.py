# Copyright 2018 Michael J Simms
"""Schedules computationally expensive analysis tasks"""

import json
import threading
import time
import DataMgr
from bson.json_util import dumps
from ActivityAnalyzer import analyze_activity

class AnalysisScheduler(threading.Thread):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self, data_mgr):
        self.quitting = False
        self.data_mgr = data_mgr
        self.mutex = threading.Lock()
        self.queue = []
        self.enabled = True
        threading.Thread.__init__(self)

    def terminate(self):
        """Destructor"""
        print("Terminating the analysis scheduler...")
        self.queue = []
        self.quitting = True

    def queue_depth(self):
        """Returns the number of items in the queue."""
        result = 0
        self.mutex.acquire()
        try:
            result = len(self.queue)
        finally:
            self.mutex.release()
        return result

    def add_to_queue(self, activity_id, activity):
        """Adds the activity ID to the list of activities to be analyzed."""
        if not self.enabled:
            return
        analysis_obj = analyze_activity.delay(dumps(activity))
        self.mutex.acquire()
        try:
            analysis_pair = (activity_id, analysis_obj)
            self.queue.append(analysis_pair)
        finally:
            self.mutex.release()

    def run(self):
        """Main run loop."""
        while not self.quitting:
            self.mutex.acquire()
            try:
                new_queue = []
                for activity_id, analysis_obj in self.queue:
                    if analysis_obj.ready() is True:
                        self.data_mgr.create_activity_summary(activity_id, analysis_obj.result)
                    else:
                        analysis_pair = (activity_id, analysis_obj)
                        new_queue.append(analysis_pair)
                self.queue = new_queue
            finally:
                self.mutex.release()
            time.sleep(1)
