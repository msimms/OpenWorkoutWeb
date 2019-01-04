# Copyright 2018 Michael J Simms
"""Schedules computationally expensive import tasks"""

import os
import threading
import time

class ImportWorker(threading.Thread):
    """Class for scheduling computationally expensive import tasks."""

    def __init__(self, data_mgr, username, user_id, local_file_name, uploaded_file_name, file_extension):
        threading.Thread.__init__(self)
        self.data_mgr = data_mgr
        self.username = username
        self.user_id = user_id
        self.local_file_name = local_file_name
        self.uploaded_file_name = uploaded_file_name
        self.file_extension = file_extension

    def run(self):
        """Main run loop."""
        try:
            importer = Importer.Importer(data_mgr)
            importer.import_file(self.username, self.user_id, self.local_file_name, self.uploaded_file_name, self.file_extension)
        finally:
            # Remove the local file.
            os.remove(self.local_file_name)

class ImportScheduler(threading.Thread):
    """Class for scheduling computationally expensive import tasks."""

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
        print("Terminating the import scheduler...")
        self.queue = []
        self.quitting = True

    def queue_depth(self):
        """Returns the number of items in the queue."""
        result = 0
        self.mutex.acquire()
        try:
            result = len(self.workers)
        finally:
            self.mutex.release()
        return result

    def add_to_queue(self, username, user_id, local_file_name, uploaded_file_name, file_extension):
        """Adds the activity ID to the list of activities to be analyzed."""
        params = {}
        params['username'] = username
        params['user_id'] = user_id
        params['local_file_name'] = local_file_name
        params['uploaded_file_name'] = uploaded_file_name
        params['file_extension'] = file_extension

        self.mutex.acquire()
        try:
            self.queue.append(params)
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
                    params = self.queue.pop(0)
                    worker = ImportWorker(self.data_mgr, params['username'], params['user_id'], params['local_file_name'], params['uploaded_file_name'], params['file_extension'])
                    self.workers.append(worker)
                    worker.start()
            finally:
                self.mutex.release()
            time.sleep(1)
