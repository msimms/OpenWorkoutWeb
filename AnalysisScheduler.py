# Copyright 2018 Michael J Simms
"""Schedules computationally expensive analysis tasks"""

import threading
import time
import ActivityAnalyzer
import DataMgr

class AnalysisScheduler(threading.Thread):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self, data_mgr, max_worker_threads):
        threading.Thread.__init__(self)
        self.quitting = False
        self.data_mgr = data_mgr
        self.max_worker_threads = max_worker_threads
        self.mutex = threading.Lock()
        self.queue = []
        self.workers = []

    def terminate(self):
        """Destructor"""
        print("Terminating the analysis scheduler...")
        self.queue = []
        self.quitting = True
        print("Terminating analysis workers...")
        self.mutex.acquire()
        try:
            self.max_worker_threads = 0
            for worker in self.workers:
                worker.quitting = True
                worker.join()
            self.workers = []
        finally:
            self.mutex.release()

    def queue_depth(self):
        """Returns the number of items in the queue."""
        result = 0
        self.mutex.acquire()
        try:
            result = len(self.workers)
        finally:
            self.mutex.release()
        return result

    def add_to_queue(self, activity_id):
        """Adds the activity ID to the list of activities to be analyzed."""
        self.mutex.acquire()
        try:
            # Is this item currently being worked?
            being_worked = False
            for worker in self.workers:
                if worker.activity_id == activity_id:
                    being_worked = True

            if not (being_worked or activity_id in self.queue):
                self.queue.append(activity_id)
        finally:
            self.mutex.release()

    def run(self):
        """Main run loop."""
        while not self.quitting:
            self.mutex.acquire()
            try:
                # Remove old worker threads.
                for worker in self.workers:
                    if not worker.isAlive():
                        worker.join()
                        self.workers.remove(worker)

                # Assign more work.
                if len(self.workers) < self.max_worker_threads and len(self.queue) > 0:
                    activity_id = self.queue.pop(0)
                    worker = ActivityAnalyzer.ActivityAnalyzer(self.data_mgr, activity_id)
                    self.workers.append(worker)
                    worker.start()
            finally:
                self.mutex.release()
            time.sleep(1)
