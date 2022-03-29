# Copyright 2018 Michael J Simms
"""Handles computationally expensive analysis tasks. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import datetime
import json
import logging
import os
import sys
import time
import traceback
import ActivityHasher
import Config
import DataMgr
import IntensityCalculator
import Keys
import LocationAnalyzer
import SensorAnalyzerFactory
import Units
import UserMgr

class ActivityAnalyzer(object):
    """Class for performing the computationally expensive activity analysis task."""

    def __init__(self, activity, internal_task_id):
        self.activity = activity
        self.internal_task_id = internal_task_id # For tracking the status of the analysis
        self.summary_data = {}
        self.speed_graph = None
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr(config=Config.Config(), root_url="file://" + root_dir, analysis_scheduler=None, import_scheduler=None, workout_plan_gen_scheduler=None)
        self.user_mgr = UserMgr.UserMgr(config=Config.Config(), session_mgr=None)
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
            self.log_error("The activity object was not provided.")
            return

        try:
            # So we only do this once.
            now = datetime.datetime.utcnow()

            # Want the variable in scope, but will set it later.
            activity_id = None

            # Determine the activity type.
            if Keys.ACTIVITY_TYPE_KEY in self.activity:
                activity_type = self.activity[Keys.ACTIVITY_TYPE_KEY]
            else:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY

            # Determine the activity user.
            activity_user_id = None
            if Keys.ACTIVITY_USER_ID_KEY in self.activity:
                activity_user_id = str(self.activity[Keys.ACTIVITY_USER_ID_KEY])

            # Activity ID is not set, or is not valid. Try to sort it out.
            if activity_user_id is None:
                self.log_error("The activity user ID was not provided.")
                return

            # Update the status of the analysis in the database.
            self.data_mgr.update_deferred_task(activity_user_id, self.internal_task_id, activity_id, Keys.TASK_STATUS_STARTED)

            # Make sure the activity start time is set.
            print("Computing the start time...")
            start_time_secs = self.data_mgr.update_activity_start_time(self.activity)

            # We'll use this to compute the end time.
            end_time_ms = 0

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

                    # Required elements.
                    end_time_ms = location[Keys.LOCATION_TIME_KEY]
                    latitude = location[Keys.LOCATION_LAT_KEY]
                    longitude = location[Keys.LOCATION_LON_KEY]
                    altitude = location[Keys.LOCATION_ALT_KEY]

                    # Optional elements.
                    horizontal_accuracy = 0.0
                    vertical_accuracy = 0.0
                    if Keys.LOCATION_HORIZONTAL_ACCURACY_KEY in location:
                        horizontal_accuracy = location[Keys.LOCATION_HORIZONTAL_ACCURACY_KEY]
                    if Keys.LOCATION_VERTICAL_ACCURACY_KEY in location:
                        vertical_accuracy = location[Keys.LOCATION_VERTICAL_ACCURACY_KEY]

                    # Update the analyzer.
                    location_analyzer.append_location(end_time_ms, latitude, longitude, altitude, horizontal_accuracy, vertical_accuracy)
                    location_analyzer.update_speeds()

                    self.should_yield()
                self.summary_data.update(location_analyzer.analyze())
            self.should_yield()

            # Do the sensor analysis.
            print("Performing sensor analysis...")
            sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
            for sensor_type in sensor_types_to_analyze:
                if sensor_type in self.activity:
                    print("Analyzing " + sensor_type + " data...")

                    try:
                        # Do the analysis.
                        sensor_analyzer = SensorAnalyzerFactory.create_with_data(sensor_type, self.activity[sensor_type], activity_type, activity_user_id, self.data_mgr, self.user_mgr)

                        # Save the results to the database.
                        self.summary_data.update(sensor_analyzer.analyze())

                        # Did we find the maximum heart rate. If so, add it to the list of calculated maximums.
                        # This list will be used to compute the user's estimated maximum heart rate.
                        if sensor_type == Keys.APP_HEART_RATE_KEY:

                            existing_max_hrs = self.user_mgr.retrieve_user_setting(activity_user_id, Keys.ESTIMATED_MAX_HEART_RATE_LIST_KEY)
                            existing_max_hrs[str(sensor_analyzer.max_time)] = sensor_analyzer.max
                            self.user_mgr.update_user_setting(activity_user_id, Keys.ESTIMATED_MAX_HEART_RATE_LIST_KEY, existing_max_hrs, now)

                        # Did we find the power meter for a cycling activity. If so, find the best 20 minute power.
                        # This list will be used to compute the user's estimated FTP.
                        if sensor_type == Keys.APP_POWER_KEY and activity_type in Keys.CYCLING_ACTIVITIES and Keys.BEST_20_MIN_POWER in self.summary_data:

                            existing_20_minute_power_bests = self.user_mgr.retrieve_user_setting(activity_user_id, Keys.BEST_CYCLING_20_MINUTE_POWER_LIST_KEY)
                            existing_20_minute_power_bests[str(sensor_analyzer.max_time)] = self.summary_data[Keys.BEST_20_MIN_POWER]
                            self.user_mgr.update_user_setting(activity_user_id, Keys.BEST_CYCLING_20_MINUTE_POWER_LIST_KEY, existing_20_minute_power_bests, now)

                    except:
                        self.log_error("Exception when analyzing activity " + sensor_type + " data.")
                        self.log_error(traceback.format_exc())
                        self.log_error(sys.exc_info()[0])
                    self.should_yield()
            self.should_yield()

            # The following require us to have an activity ID.
            if Keys.ACTIVITY_ID_KEY in self.activity:

                # Unique identifier for the activity.
                activity_id = self.activity[Keys.ACTIVITY_ID_KEY]

                # Create a current speed graph - if one has not already been created.
                if Keys.APP_CURRENT_SPEED_KEY not in self.activity and location_analyzer is not None:

                    print("Creating the speed graph...")
                    self.speed_graph = location_analyzer.create_speed_graph()

                    print("Storing the speed graph...")
                    if not self.data_mgr.create_activity_metadata_list(activity_id, Keys.APP_CURRENT_SPEED_KEY, self.speed_graph):
                        self.log_error("Error returned when saving activity speed graph.")

                    print("Storing the distance calculations...")
                    if not self.data_mgr.create_activity_metadata_list(activity_id, Keys.APP_DISTANCES_KEY, location_analyzer.distance_buf):
                        self.log_error("Error returned when saving activity speed graph.")                    
                self.should_yield()

                # Where was this activity performed?
                print("Computing the location description...")
                location_description = self.data_mgr.get_location_description(activity_id)
                self.summary_data[Keys.ACTIVITY_LOCATION_DESCRIPTION_KEY] = location_description
                self.should_yield()

                # Was a stress score calculated (i.e., did the activity have power data from which stress could be computed)?
                # If not, estimate a stress score.
                print("Update the end time...")
                end_time_secs = end_time_ms / 1000
                if end_time_ms > 0:
                    self.data_mgr.update_activity_end_time(self.activity, end_time_secs)

                # If activity duration and distance have been calculated.
                print("Computing the intensity score and training paces...")
                if start_time_secs > 0 and end_time_secs > 0 and end_time_secs > start_time_secs and len(location_analyzer.distance_buf) > 0:

                    # These are used by both cycling and running intensity calculations.
                    distance_entry = location_analyzer.distance_buf[-1]
                    workout_duration_secs = end_time_secs - start_time_secs
                    avg_workout_pace_meters_per_sec =  distance_entry[1] / workout_duration_secs

                    # Running activity.
                    if activity_type in Keys.RUNNING_ACTIVITIES:

                        # Compute training paces.
                        print("* (Re)computing the training paces...")
                        _, running_bests, _, _ = self.data_mgr.retrieve_recent_bests(activity_user_id, DataMgr.SIX_MONTHS)
                        run_paces = self.data_mgr.compute_run_training_paces(activity_user_id, running_bests)

                        # We need to know the user's threshold pace to compute the intensity score.
                        print("* Computing the intensity score...")
                        if Keys.FUNCTIONAL_THRESHOLD_PACE in run_paces:
                            threshold_pace_meters_per_hour = run_paces[Keys.FUNCTIONAL_THRESHOLD_PACE] * 60.0
                            calc = IntensityCalculator.IntensityCalculator()
                            stress = calc.estimate_intensity_score(workout_duration_secs, avg_workout_pace_meters_per_sec, threshold_pace_meters_per_hour)
                            self.summary_data[Keys.INTENSITY_SCORE] = stress

                    # Cycling activity.
                    elif activity_type in Keys.CYCLING_ACTIVITIES:
                        pass

                # Store the results.
                print("Storing the activity summary...")
                if not self.data_mgr.create_activity_summary(activity_id, self.summary_data):
                    self.log_error("Error returned when saving activity summary data: " + str(self.summary_data))
            else:
                self.log_error("Activity ID not provided. Cannot create activity summary.")
            self.should_yield()

            # Update personal bests.
            if Keys.ACTIVITY_START_TIME_KEY in self.activity:
                print("Updating personal bests...")
                activity_time = self.activity[Keys.ACTIVITY_START_TIME_KEY]

                # Cleaning up the activity summary cache is expensive so don't do it if it was done recently.
                last_pruned_time = self.user_mgr.retrieve_user_setting(activity_user_id, Keys.USER_ACTIVITY_SUMMARY_CACHE_LAST_PRUNED)
                prune_activity_summary_cache = (now - last_pruned_time).total_seconds() > Units.SECS_PER_DAY
                if prune_activity_summary_cache:
                    print("Will prune the activity summaries...")
                    self.user_mgr.update_user_setting(activity_user_id, Keys.USER_ACTIVITY_SUMMARY_CACHE_LAST_PRUNED, now, now)

                if not self.data_mgr.update_activity_bests_and_personal_records_cache(activity_user_id, activity_id, activity_type, activity_time, self.summary_data, prune_activity_summary_cache):
                    self.log_error("Error returned when updating personal records.")
            else:
                self.log_error("Activity time not provided. Cannot update personal records.")

            # Update the status of the analysis in the database.
            self.data_mgr.update_deferred_task(activity_user_id, self.internal_task_id, activity_id, Keys.TASK_STATUS_FINISHED)
        except:
            self.log_error("Exception when analyzing activity data: " + str(self.summary_data))
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])

@celery_worker.task(ignore_result=True)
def analyze_activity(activity_str, internal_task_id):
    print("Starting activity analysis...")
    activity_obj = json.loads(activity_str)
    analyzer = ActivityAnalyzer(activity_obj, internal_task_id)
    analyzer.perform_analysis()
    print("Activity analysis finished")

def main():
    """Entry point for an analysis worker."""
    pass

if __name__ == "__main__":
    main()
