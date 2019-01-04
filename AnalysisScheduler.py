# Copyright 2018 Michael J Simms
"""Schedules computationally expensive analysis tasks"""

import json
import logging
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

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

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
        analysis_pair = (activity_id, analysis_obj)

        self.mutex.acquire()
        try:
            self.queue.append(analysis_pair)
        finally:
            self.mutex.release()

    def store_results(self, activity_id, summary_data):
        """Called after analysis is complete. Stores the summary data in the database."""
        try:
            if not self.data_mgr.create_activity_summary(activity_id, summary_data):
                self.log_error("Error returned when saving activity summary data: " + str(summary_data))
        except:
            self.log_error("Exception when saving activity summary data: " + str(summary_data))

    def run(self):
        """Main run loop."""
        while not self.quitting:
            old_queue = []
            new_queue = []

            self.mutex.acquire()
            try:
                old_queue = self.queue
            finally:
                self.mutex.release()

            try:
                for activity_id, analysis_obj in old_queue:
                    if analysis_obj.ready() is True:
                        summary_data = json.loads(analysis_obj.result)
                        self.store_results(activity_id, summary_data)
                    else:
                        analysis_pair = (activity_id, analysis_obj)
                        new_queue.append(analysis_pair)
            except:
                self.log_error("Exception when checking analysis queue")

            self.mutex.acquire()
            try:
                self.queue.extend(new_queue)
            finally:
                self.mutex.release()

            time.sleep(3)
