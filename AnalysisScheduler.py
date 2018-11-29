# Copyright 2018 Michael J Simms
"""Schedules computationally expensive analysis tasks"""

import threading
import time
import DataMgr
import Keys
import LocationAnalyzer
import SensorAnalyzerFactory

class AnalysisWorker(threading.Thread):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self, data_mgr, activity_id):
        threading.Thread.__init__(self)
        self.data_mgr = data_mgr
        self.activity_id = activity_id
        self.quitting = False

    def terminate(self):
        """Destructor"""
        print("Terminating an analysis worker")

    def run(self):
        """Main run loop."""

        # Load the activity from the database.
        activity = self.data_mgr.retrieve_activity(self.activity_id)
        if activity is not None:
            summary_data = {}

            # Determine the activity type.
            if Keys.ACTIVITY_TYPE_KEY in activity:
                activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
            else:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY

            # Check for interrupt.
            if self.quitting:
                return

            # Do the location analysis.
            if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                location_analyzer = LocationAnalyzer.LocationAnalyzer(activity_type)
                locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
                for location in locations:
                    date_time = location[Keys.LOCATION_TIME_KEY]
                    latitude = location[Keys.LOCATION_LAT_KEY]
                    longitude = location[Keys.LOCATION_LON_KEY]
                    altitude = location[Keys.LOCATION_ALT_KEY]
                    location_analyzer.append_location(date_time, latitude, longitude, altitude)
                    location_analyzer.update_speeds()
                summary_data.update(location_analyzer.analyze())

            # Check for interrupt.
            if self.quitting:
                return

            # Do the accelerometer analysis.
            if Keys.APP_ACCELEROMETER_KEY in activity:
                pass

            # Check for interrupt.
            if self.quitting:
                return

            # Do the sensor analysis.
            sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
            for sensor_type in sensor_types_to_analyze:
                if sensor_type in activity:
                    sensor_analyzer = SensorAnalyzerFactory.create_with_data(sensor_analyzer, activity[sensor_type])
                    summary_data.update(sensor_analyzer.analyze())

            # Save the results.
            self.data_mgr.create_activity_summary(self.activity_id, summary_data)

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
                    worker = AnalysisWorker(self.data_mgr, activity_id)
                    self.workers.append(worker)
                    worker.start()
            finally:
                self.mutex.release()
            time.sleep(1)
