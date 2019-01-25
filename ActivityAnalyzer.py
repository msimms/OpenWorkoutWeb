# Copyright 2018 Michael J Simms
"""Handles computationally expensive analysis tasks"""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import logging
import os
import sys
import time
import traceback
import DataMgr
import Keys
import LocationAnalyzer
import SensorAnalyzerFactory

class ActivityAnalyzer(object):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self, activity):
        self.activity = activity
        self.summary_data = {}
        self.speed_graph = None
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr(root_dir, None, None)
        super(ActivityAnalyzer, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        print(log_str)
        logger = logging.getLogger()
        if logger is not None:
            logger.debug(log_str)

    def perform_analysis(self):
        """Main analysis routine."""

        # Sanity check.
        if self.activity is None:
            return

        try:
            # Determine the activity type.
            if Keys.ACTIVITY_TYPE_KEY in self.activity:
                activity_type = self.activity[Keys.ACTIVITY_TYPE_KEY]
            else:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY

            # Do the location analysis.
            print("Performing location analysis...")
            if Keys.ACTIVITY_LOCATIONS_KEY in self.activity:
                location_analyzer = LocationAnalyzer.LocationAnalyzer(activity_type)
                locations = self.activity[Keys.ACTIVITY_LOCATIONS_KEY]
                for location in locations:
                    date_time = location[Keys.LOCATION_TIME_KEY]
                    latitude = location[Keys.LOCATION_LAT_KEY]
                    longitude = location[Keys.LOCATION_LON_KEY]
                    altitude = location[Keys.LOCATION_ALT_KEY]
                    location_analyzer.append_location(date_time, latitude, longitude, altitude)
                    location_analyzer.update_speeds()
                self.summary_data.update(location_analyzer.analyze())
            time.sleep(1) # Yield the GIL. Filty hack that stops Celery from crashing because of timeout errors when overloaded

            # Do the sensor analysis.
            print("Performing sensor analysis...")
            sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
            for sensor_type in sensor_types_to_analyze:
                if sensor_type in self.activity:
                    sensor_analyzer = SensorAnalyzerFactory.create_with_data(sensor_type, self.activity[sensor_type], activity_type)
                    self.summary_data.update(sensor_analyzer.analyze())
            time.sleep(1) # Yield the GIL. 

            # Create a current speed graph - if one has not already been created.
            print("Creating speed graph...")
            if Keys.APP_CURRENT_SPEED_KEY not in self.activity:
                self.speed_graph = location_analyzer.create_speed_graph()
            time.sleep(1) # Yield the GIL. 

            # Store the results.
            print("Storing results...")
            if Keys.ACTIVITY_ID_KEY in self.activity:
                activity_id = self.activity[Keys.ACTIVITY_ID_KEY]
                if not self.data_mgr.create_activity_summary(activity_id, self.summary_data):
                    self.log_error("Error returned when saving activity summary data: " + str(self.summary_data))
            else:
                self.log_error("Activity ID not provided. Cannot create activity summary.")

            # Update personal bests
            print("Updating personal bests...")
            if Keys.ACTIVITY_USER_ID_KEY in self.activity and Keys.ACTIVITY_TIME_KEY in self.activity:
                user_id = self.activity[Keys.ACTIVITY_USER_ID_KEY]
                activity_time = self.activity[Keys.ACTIVITY_TIME_KEY]
                if not self.data_mgr.insert_bests_from_activity(user_id, activity_id, activity_type, activity_time, self.summary_data):
                    self.log_error("Error returned when updating personal records.")
            else:
                self.log_error("User ID or activity time not provided. Cannot update personal records.")
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error("Exception when analyzing activity data: " + str(self.summary_data))
            self.log_error(sys.exc_info()[0])

@celery_worker.task()
def analyze_activity(activity_str):
    print("Starting activity analysis...")
    activity_obj = json.loads(activity_str)
    analyzer = ActivityAnalyzer(activity_obj)
    analyzer.perform_analysis()
    print("Activity analysis finished")

def main():
    """Entry point for an analysis worker."""
    pass

if __name__ == "__main__":
    main()
