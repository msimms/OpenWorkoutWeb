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
                self.join_worker_thread(worker)
            self.workers = []
        finally:
            self.mutex.release()

    def join_worker_thread(self, worker):
        """Handles a completed thread."""

        # Wait for the thread to finish.
        worker.join()

        # Save the summary results.
        self.data_mgr.create_activity_summary(worker.activity_id, worker.summary_data)

        # Save the current speed graph - if one has not already been created.
        if Keys.APP_CURRENT_SPEED_KEY not in worker.activity:
            self.data_mgr.create_metadata_list(worker.activity_id, Keys.APP_CURRENT_SPEED_KEY, worker.speed_graph)

        # Done, remove it from the queue.
        self.workers.remove(worker)

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
                        self.join_worker_thread(worker)

                # Assign more work.
                if len(self.workers) < self.max_worker_threads and len(self.queue) > 0:
                    activity_id = self.queue.pop(0)
                    activity = self.data_mgr.retrieve_activity(activity_id)
                    worker = ActivityAnalyzer.ActivityAnalyzer(activity, activity_id)
                    self.workers.append(worker)
                    worker.start()
            finally:
                self.mutex.release()
            time.sleep(1)
