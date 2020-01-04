# Copyright 2018 Michael J Simms
"""Handles computationally expensive analysis tasks. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import logging
import os
import sys
import time
import traceback
import ActivityHasher
import DataMgr
import Keys
import LocationAnalyzer
import SensorAnalyzerFactory

class ActivityAnalyzer(object):
    """Class for performing the computationally expensive activity analysis task."""

    def __init__(self, activity):
        self.activity = activity
        self.summary_data = {}
        self.speed_graph = None
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr("file://" + root_dir, root_dir, None, None, None)
        self.last_yield = time.time()
        super(ActivityAnalyzer, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        print(log_str)
        logger = logging.getLogger()
        if logger is not None:
            logger.debug(log_str)

    def should_yield(self):
        """Used to periodically yeild the GIL, because python sucks."""
        if time.time() - self.last_yield > 3:
            time.sleep(0)
            self.last_yield = time.time()

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

            # Determine the activity user.
            activity_user_id = None
            if Keys.ACTIVITY_USER_ID_KEY in self.activity:
                activity_user_id = str(self.activity[Keys.ACTIVITY_USER_ID_KEY])

            # Hash the activity.
            print("Hashing the activity...")
            hasher = ActivityHasher.ActivityHasher(self.activity)
            hash_str = hasher.hash()
            self.summary_data[Keys.ACTIVITY_HASH_KEY] = hash_str
            self.should_yield()

            # Do the location analysis.
            print("Performing location analysis...")
            location_analyzer = None
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
                    self.should_yield()
                self.summary_data.update(location_analyzer.analyze())
            self.should_yield()

            # Do the sensor analysis.
            print("Performing sensor analysis...")
            sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
            for sensor_type in sensor_types_to_analyze:
                if sensor_type in self.activity:
                    sensor_analyzer = SensorAnalyzerFactory.create_with_data(sensor_type, self.activity[sensor_type], activity_type, activity_user_id, self.data_mgr)
                    self.summary_data.update(sensor_analyzer.analyze())
                    self.should_yield()
            self.should_yield()

            # The following require us to have an activity ID.
            if Keys.ACTIVITY_ID_KEY in self.activity:
                activity_id = self.activity[Keys.ACTIVITY_ID_KEY]

                # Create a current speed graph - if one has not already been created.
                if Keys.APP_CURRENT_SPEED_KEY not in self.activity and location_analyzer is not None:
                    print("Creating speed graph...")
                    self.speed_graph = location_analyzer.create_speed_graph()

                    print("Storing the speed graph...")
                    if not self.data_mgr.create_metadata_list(activity_id, Keys.APP_CURRENT_SPEED_KEY, self.speed_graph):
                        self.log_error("Error returned when saving activity speed graph.")

                    print("Storing distance calculations...")
                    if not self.data_mgr.create_metadata_list(activity_id, Keys.APP_DISTANCES_KEY, location_analyzer.distance_buf):
                        self.log_error("Error returned when saving activity speed graph.")                    
                self.should_yield()

                # Where was this activity performed?
                print("Computing location description...")
                location_description = self.data_mgr.get_location_description(activity_id)
                self.summary_data[Keys.ACTIVITY_LOCATION_DESCRIPTION_KEY] = location_description

                # Store the results.
                print("Storing results...")
                if not self.data_mgr.create_activity_summary(activity_id, self.summary_data):
                    self.log_error("Error returned when saving activity summary data: " + str(self.summary_data))
            else:
                self.log_error("Activity ID not provided. Cannot create activity summary.")
            self.should_yield()

            # Update personal bests.
            print("Updating personal bests...")
            if activity_user_id and Keys.ACTIVITY_TIME_KEY in self.activity:
                activity_time = self.activity[Keys.ACTIVITY_TIME_KEY]
                if not self.data_mgr.update_bests_for_activity(activity_user_id, activity_id, activity_type, activity_time, self.summary_data):
                    self.log_error("Error returned when updating personal records.")
            else:
                self.log_error("User ID or activity time not provided. Cannot update personal records.")
        except:
            self.log_error("Exception when analyzing activity data: " + str(self.summary_data))
            self.log_error(traceback.format_exc())
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
