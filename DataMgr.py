# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2017-2020 Mike Simms
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
"""Data store abstraction"""

import hashlib
import os
import time
import uuid
import BmiCalculator
import FtpCalculator
import HeartRateCalculator
import Importer
import Keys
import MapSearch
import StraenDb
import Summarizer
import TrainingPaceCalculator
import VO2MaxCalculator
import celery
from celery import states

SIX_MONTHS = ((365.25 / 2.0) * 24.0 * 60.0 * 60.0)
ONE_YEAR = (365.25 * 24.0 * 60.0 * 60.0)
ONE_WEEK = (7.0 * 24.0 * 60.0 * 60.0)
FOUR_WEEKS = (28.0 * 24.0 * 60.0 * 60.0)

def get_activities_sort_key(item):
    # Was the start time provided? If not, look at the first location.
    if Keys.ACTIVITY_START_TIME_KEY in item:
        return item[Keys.ACTIVITY_START_TIME_KEY]
    return 0

class DataMgr(Importer.ActivityWriter):
    """Data store abstraction"""

    def __init__(self, config, root_url, analysis_scheduler, import_scheduler, workout_plan_gen_scheduler):
        self.config = config
        self.root_url = root_url
        self.analysis_scheduler = analysis_scheduler
        self.import_scheduler = import_scheduler
        self.workout_plan_gen_scheduler = workout_plan_gen_scheduler
        self.database = StraenDb.MongoDatabase()
        self.database.connect()
        self.map_search = None
        self.celery_worker = celery.Celery('straen_worker')
        self.celery_worker.config_from_object('CeleryConfig')
        if config is not None:
            self.celery_worker.conf.broker_url = config.get_broker_url()
        super(Importer.ActivityWriter, self).__init__()

    def terminate(self):
        """Destructor"""
        self.analysis_scheduler = None
        self.import_scheduler = None
        self.workout_plan_gen_scheduler = None
        self.database = None

    def total_users_count(self):
        """Returns the number of users in the database."""
        return self.database.total_users_count()

    def total_activities_count(self):
        """Returns the number of activities in the database."""
        return self.database.total_activities_count()

    def create_activity_id(self):
        """Generates a new activity ID."""
        return str(uuid.uuid4())

    def analyze_activity(self, activity, activity_user_id):
        """Schedules the specified activity for analysis."""
        activity[Keys.ACTIVITY_USER_ID_KEY] = activity_user_id
        self.analysis_scheduler.add_activity_to_queue(activity, activity_user_id, self)

    def compute_activity_end_time(self, activity):
        """Examines the activity and computes the time at which the activity ended."""
        end_time = None

        # Look through activity attributes that have a "time".
        search_keys = []
        search_keys.append(Keys.APP_LOCATIONS_KEY)
        search_keys.append(Keys.APP_ACCELEROMETER_KEY)
        for search_key in search_keys:
            if search_key in activity and isinstance(activity[search_key], list) and len(activity[search_key]) > 0:
                last_entry = (activity[search_key])[-1]
                if "time" in last_entry:
                    possible_end_time = last_entry["time"]
                    if end_time is None or possible_end_time > end_time:
                        end_time = possible_end_time

        return end_time

    def compute_and_store_activity_end_time(self, activity):
        """Examines the activity and computes the time at which the activity ended, storing it so we don't have to do this again."""
        if self.database is None:
            raise Exception("No database.")

        end_time = self.compute_activity_end_time(activity)

        # If we couldn't find anything with a time then just duplicate the start time, assuming it's a manually entered workout or something.
        if end_time is None:
            end_time = activity[Keys.ACTIVITY_START_TIME_KEY]

        # Store the end time, so we don't have to go through this again.
        if end_time is not None:
            activity_id = activity[Keys.ACTIVITY_ID_KEY]
            self.database.create_activity_metadata(activity_id, end_time, Keys.ACTIVITY_END_TIME_KEY, end_time / 1000, False)

        return end_time

    def is_duplicate_activity(self, user_id, start_time):
        """Inherited from ActivityWriter. Returns TRUE if the activity appears to be a duplicate of another activity. Returns FALSE otherwise."""
        if self.database is None:
            raise Exception("No database.")

        activities = self.database.retrieve_user_activity_list(user_id, None, None, None)
        for activity in activities:

            if Keys.ACTIVITY_START_TIME_KEY in activity:

                # Get the activity start and end times.
                activity_start_time = activity[Keys.ACTIVITY_START_TIME_KEY]
                if Keys.ACTIVITY_END_TIME_KEY not in activity:
                    activity_end_time = self.compute_and_store_activity_end_time(activity)
                else:
                    activity_end_time = activity[Keys.ACTIVITY_END_TIME_KEY]

                # We're looking for activities that start within the bounds of another activity.
                if start_time >= activity_start_time and start_time < activity_end_time:
                    return True

        return False

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time):
        """Inherited from ActivityWriter. Called when we start reading an activity file."""
        if self.database is None:
            raise Exception("No database.")

        device_str = ""
        activity_id = self.create_activity_id()
        if stream_name is None:
            stream_name = ""

        if not self.database.create_activity(activity_id, stream_name, start_time, device_str):
            return None, None
        if activity_type is not None and len(activity_type) > 0:
            self.database.create_activity_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, activity_type, False)
            self.create_default_tags_on_activity(user_id, activity_type, activity_id)
        if user_id is not None:
            self.database.create_activity_metadata(activity_id, 0, Keys.ACTIVITY_USER_ID_KEY, user_id, False)
        return device_str, activity_id

    def create_activity_track(self, device_str, activity_id, track_name, track_description):
        """Inherited from ActivityWriter."""
        pass

    def create_activity_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Inherited from ActivityWriter. Create method for a location."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_activity_location(device_str, activity_id, date_time, latitude, longitude, altitude)

    def create_activity_locations(self, device_str, activity_id, locations):
        """Inherited from ActivityWriter. Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_locations(device_str, activity_id, locations)

    def create_activity_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Inherited from ActivityWriter. Create method for sensor data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_sensor_reading(activity_id, date_time, sensor_type, value)

    def create_activity_sensor_readings(self, activity_id, sensor_type, values):
        """Inherited from ActivityWriter. Adds several sensor readings to the database. 'values' is an array of arrays in the form [time, value]."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_sensor_readings(activity_id, sensor_type, values)

    def create_activity_event(self, activity_id, event):
        """Inherited from ActivityWriter. 'event' is a dictionary describing an event."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        if event is None:
            raise Exception("No event.")
        return self.database.create_activity_events(activity_id, event)

    def create_activity_events(self, activity_id, events):
        """Inherited from ActivityWriter. 'events' is an array of dictionaries in which each dictionary describes an event."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        if events is None:
            raise Exception("No events.")
        return self.database.create_activity_events(activity_id, events)

    def create_activity_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_metadata(activity_id, date_time, key, value, create_list)

    def create_activity_metadata_list(self, activity_id, key, values):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_metadata_list(activity_id, key, values)

    def create_activity_sets_and_reps_data(self, activity_id, sets):
        """Create method for activity set and rep data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_sets_and_reps_data(activity_id, sets)

    def create_activity_accelerometer_reading(self, device_str, activity_id, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_accelerometer_reading(device_str, activity_id, accels)

    def finish_activity(self, activity_id, end_time):
        """Inherited from ActivityWriter. Called for post-processing."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_activity_metadata(activity_id, end_time, Keys.ACTIVITY_END_TIME_KEY, end_time / 1000, False)

    def create_deferred_task(self, user_id, task_type, celery_task_id, internal_task_id, details):
        """Called by the importer to store data associated with an ongoing import task."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("No user ID.")
        if task_type is None:
            raise Exception("No task type.")
        if celery_task_id is None:
            raise Exception("No celery task ID.")
        if internal_task_id is None:
            raise Exception("No internal task ID.")
        return self.database.create_deferred_task(user_id, task_type, celery_task_id, internal_task_id, details, Keys.TASK_STATUS_QUEUED)

    def retrieve_deferred_tasks(self, user_id):
        """Returns a list of all incomplete tasks."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("No user ID.")
        return self.database.retrieve_deferred_tasks(user_id)

    def update_deferred_task(self, user_id, internal_task_id, status):
        """Returns a list of all incomplete tasks."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("No user ID.")
        if internal_task_id is None:
            raise Exception("No internal task ID.")
        if status is None:
            raise Exception("No status.")
        return self.database.update_deferred_task(user_id, internal_task_id, status)

    def prune_deferred_tasks_list(self):
        """Removes all completed tasks from the list."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.delete_finished_deferred_tasks()

    def create_uploaded_file(self, activity_id, file_data):
        """Create method for an uploaded activity file."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity_id")
        if file_data is None:
            raise Exception("No file data")
        return self.database.create_uploaded_file(activity_id, file_data)

    def import_file(self, username, user_id, uploaded_file_data, uploaded_file_name):
        """Imports the contents of a local file into the database."""
        if self.import_scheduler is None:
            raise Exception("No importer.")
        if self.config is None:
            raise Exception("No configuration object.")
        if username is None:
            raise Exception("No username.")
        if user_id is None:
            raise Exception("No user ID.")
        if uploaded_file_data is None:
            raise Exception("No uploaded file data.")
        if uploaded_file_name is None:
            raise Exception("No uploaded file name.")

        # Check the file size.
        if len(uploaded_file_data) > self.config.get_import_max_file_size():
            raise Exception("The file is too large.")

        return self.import_scheduler.add_file_to_queue(username, user_id, uploaded_file_data, uploaded_file_name, self)

    def attach_photo_to_activity(self, user_id, uploaded_file_data, uploaded_file_name, activity_id):
        """Imports a photo and associates it with an activity."""
        if self.database is None:
            raise Exception("No database.")
        if self.config is None:
            raise Exception("No configuration object.")
        if user_id is None:
            raise Exception("No user ID.")
        if uploaded_file_data is None:
            raise Exception("No uploaded file data.")
        if activity_id is None:
            raise Exception("No activity ID.")

        # Check the file size.
        if len(uploaded_file_data) > self.config.get_photos_max_file_size():
            raise Exception("The file is too large.")

        # Hash the photo. This will prevent duplicates as well as give us a unique name.
        h = hashlib.sha512()
        h.update(uploaded_file_data)
        hash_str = h.hexdigest()

        # Where are we storing photos?
        photos_dir = self.config.get_photos_dir()
        if len(photos_dir) == 0:
            raise Exception("No photos directory.")

        # Create the directory, if it does not already exist.
        user_photos_dir = os.path.join(photos_dir, str(user_id))
        if not os.path.exists(user_photos_dir):
            os.makedirs(user_photos_dir)

        # Save the file to the user's photos directory.
        try:
            local_file_name = os.path.join(user_photos_dir, hash_str)
            with open(local_file_name, 'wb') as local_file:
                local_file.write(uploaded_file_data)
        except:
            raise Exception("Could not save the photo.")

        # Attach the hash to the activity.
        result = self.database.create_activity_photo(user_id, activity_id, hash_str)

        return result

    def list_activity_photos(self, activity_id):
        """Lists all photos associated with an activity. Response is a list of identifiers."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.list_activity_photos(activity_id)

    def update_activity_start_time(self, activity):
        """Caches the activity start time, based on the first reported location."""
        if Keys.ACTIVITY_START_TIME_KEY in activity:
            return activity[Keys.ACTIVITY_START_TIME_KEY]

        if Keys.ACTIVITY_LOCATIONS_KEY in activity:
            locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
        else:
            locations = self.retrieve_activity_locations(activity[Keys.ACTIVITY_ID_KEY])

        time_num = 0
        if len(locations) > 0:
            first_loc = locations[0]
            if Keys.LOCATION_TIME_KEY in first_loc:
                time_num = first_loc[Keys.LOCATION_TIME_KEY] / 1000 # Milliseconds to seconds
                activity_id = activity[Keys.ACTIVITY_ID_KEY]
                activity[Keys.ACTIVITY_START_TIME_KEY] = time_num
                self.create_activity_metadata(activity_id, time_num, Keys.ACTIVITY_START_TIME_KEY, time_num, False)
        return time_num

    def update_moving_activity(self, device_str, activity_id, locations, sensor_readings_dict, metadata_list_dict):
        """Updates locations, sensor readings, and metadata associated with a moving activity. Provided as a performance improvement over making several database updates."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.update_activity(device_str, activity_id, locations, sensor_readings_dict, metadata_list_dict)

    def is_activity_public(self, activity):
        """Helper function for returning whether or not an activity is publically visible."""
        if Keys.ACTIVITY_VISIBILITY_KEY in activity:
            if activity[Keys.ACTIVITY_VISIBILITY_KEY] == "private":
                return False
        return True

    def is_activity_id_public(self, activity_id):
        """Helper function for returning whether or not an activity is publically visible."""
        visibility = self.retrieve_activity_visibility(activity_id)
        if visibility is not None:
            if visibility == "private":
                return False
        return True

    def retrieve_user_activity_list(self, user_id, user_realname, start, num_results):
        """Returns a list containing all of the user's activities, up to num_results. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        activities = []

        # List activities recorded on devices registered to the user.
        devices = self.database.retrieve_user_devices(user_id)
        devices = list(set(devices)) # De-duplicate
        if devices is not None:
            for device in devices:
                device_activities = self.database.retrieve_device_activity_list(device, start, None)
                if device_activities is not None:
                    for device_activity in device_activities:
                        device_activity[Keys.REALNAME_KEY] = user_realname
                        self.update_activity_start_time(device_activity)
                    activities.extend(device_activities)

        # List activities with no device that are associated with the user.
        exclude_keys = self.database.list_excluded_activity_keys() # Things we don't need.
        user_activities = self.database.retrieve_user_activity_list(user_id, start, None, exclude_keys)
        if user_activities is not None:
            for user_activity in user_activities:
                user_activity[Keys.REALNAME_KEY] = user_realname
            activities.extend(user_activities)

        # Sort and limit the list.
        if len(activities) > 0:
            activities = sorted(activities, key=get_activities_sort_key, reverse=True)[:num_results]

        return activities

    def retrieve_each_user_activity(self, context, user_id, cb=None):
        """Fires a callback for all of the user's activities. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if context is None:
            raise Exception("Bad parameter.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if cb is None:
            raise Exception("Bad parameter.")

        # List activities recorded on devices registered to the user.
        devices = self.database.retrieve_user_devices(user_id)
        devices = list(set(devices)) # De-duplicate
        if devices is not None:
            for device in devices:
                self.database.retrieve_each_device_activity(context, user_id, device, cb)

        # List activities with no device that are associated with the user.
        self.database.retrieve_each_user_activity(context, user_id, cb)

    def retrieve_all_activities_visible_to_user(self, user_id, user_realname, start, num_results):
        """Returns a list containing all of the activities visible to the specified user, up to num_results. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        # Start with the user's own activities.
        activities = self.retrieve_user_activity_list(user_id, user_realname, start, num_results)

        # Add the activities of users they follow.
        friends = self.database.retrieve_friends(user_id)
        for friend in friends:
            more_activities = self.retrieve_user_activity_list(friend[Keys.DATABASE_ID_KEY], friend[Keys.REALNAME_KEY], start, num_results)
            for another_activity in more_activities:
                if self.is_activity_public(another_activity):
                    activities.append(another_activity)

        # Sort and limit the list.
        if len(activities) > 0:
            activities = sorted(activities, key=get_activities_sort_key, reverse=True)[:num_results]

        return activities

    def retrieve_device_activity_list(self, device_id, start, num_results):
        """Returns a list containing all of the device's activities, up to num_results. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if device_id is None or len(device_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_device_activity_list(device_id, start, num_results)

    def delete_user_gear(self, user_id):
        """Deletes all user gear."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        # TODO: Remove from each activity
        gear_list = self.database.retrieve_gear(user_id)
        for gear in gear_list:
            pass

        # Remove the gear list from the user's profile.
        return self.database.delete_all_gear(user_id)

    def delete_user_activities(self, user_id):
        """Deletes all user activities."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        devices = self.database.retrieve_user_devices(user_id)
        devices = list(set(devices)) # De-duplicate
        if devices is not None:
            for device in devices:
                self.database.delete_user_device(device)
        return True

    def retrieve_activity(self, activity_id):
        """Retrieve method for an activity, specified by the activity ID."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity(activity_id)

    def delete_activity(self, object_id, user_id, activity_id):
        """Delete the activity with the specified object ID."""
        if self.database is None:
            raise Exception("No database.")
        if object_id is None:
            raise Exception("Bad parameter.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if activity_id is None:
            raise Exception("Bad parameter.")

        # Delete the activity as well as the cache of the PRs performed during that activity.
        result = self.database.delete_activity(object_id) and self.database.delete_activity_best_for_user(user_id, activity_id)

        if result:

            # Delete the uploaded file (if any).
            self.database.delete_uploaded_file(activity_id)

            # Recreate the user's all-time PR list as the previous one could have contained data from the now deleted activity.
            result = self.refresh_user_personal_records(user_id)

        return result

    def retrieve_activity_visibility(self, device_str, activity_id):
        """Returns the visibility setting for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_visibility(device_str, activity_id)

    def update_activity_visibility(self, activity_id, visibility):
        """Changes the visibility setting for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        if visibility is None:
            raise Exception("Bad parameter.")
        return self.database.update_activity_visibility(activity_id, visibility)

    def retrieve_activity_locations(self, activity_id):
        """Returns the location list for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_locations(activity_id)

    def retrieve_activity_sensor_readings(self, key, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if self.database is None:
            raise Exception("No database.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_sensor_readings(key, activity_id)

    def retrieve_most_recent_activity_id_for_device(self, device_str):
        """Returns the most recent activity id for the specified device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")

        activity = self.database.retrieve_most_recent_activity_for_device(device_str)
        if activity is None:
            return None
        return activity[Keys.ACTIVITY_ID_KEY]

    def retrieve_most_recent_activity_for_device(self, device_str):
        """Returns the most recent activity for the specified device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_most_recent_activity_for_device(device_str)

    def retrieve_most_recent_activity_for_user(self, user_devices):
        """Returns the most recent activity id for the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_devices is None:
            raise Exception("Bad parameter.")

        most_recent_activity = None
        for device_str in user_devices:
            device_activity = self.retrieve_most_recent_activity_for_device(device_str)
            if device_activity is not None:
                if most_recent_activity is None:
                    most_recent_activity = device_activity
                elif Keys.ACTIVITY_START_TIME_KEY in device_activity and Keys.ACTIVITY_START_TIME_KEY in most_recent_activity:
                    curr_activity_time = device_activity[Keys.ACTIVITY_START_TIME_KEY]
                    prev_activity_time = most_recent_activity[Keys.ACTIVITY_START_TIME_KEY]
                    if curr_activity_time > prev_activity_time:
                        most_recent_activity = device_activity
        return most_recent_activity

    def create_activity_summary(self, activity_id, summary_data):
        """Create method for activity summary data. Summary data is data computed from the raw data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        if summary_data is None:
            raise Exception("Bad parameter.")
        return self.database.create_activity_summary(activity_id, summary_data)

    def retrieve_activity_summary(self, activity_id):
        """Retrieve method for activity summary data. Summary data is data computed from the raw data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_summary(activity_id)

    def delete_activity_summary(self, activity_id):
        """Delete method for activity summary data. Summary data is data computed from the raw data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.delete_activity_summary(activity_id)

    def list_default_tags(self):
        """Returns a list of tags that can be used for any activity."""
        tags = []
        tags.append('Race')
        tags.append('Commute')
        tags.append('Workout')
        tags.append('Interval Workout')
        tags.append('Brick Workout')
        tags.append('Hot')
        tags.append('Humid')
        tags.append('Cold')
        tags.append('Rainy')
        tags.append('Windy')
        tags.append('Virtual')
        tags.append('Group Activity')
        return tags

    def list_tags_for_activity_type_and_user(self, user_id, activity_type):
        """Returns a list of tags that are valid for a particular activity type and user."""
        tags = self.list_default_tags()
        gear_list = self.retrieve_gear(user_id)
        show_shoes = activity_type in Keys.FOOT_BASED_ACTIVITIES
        show_bikes = activity_type in Keys.CYCLING_ACTIVITIES
        if activity_type == Keys.TYPE_RUNNING_KEY:
            tags.append("Long Run")
        for gear in gear_list:
            if Keys.GEAR_TYPE_KEY in gear and Keys.GEAR_NAME_KEY in gear:
                if (show_shoes and gear[Keys.GEAR_TYPE_KEY] == Keys.GEAR_TYPE_SHOES) or (show_bikes and gear[Keys.GEAR_TYPE_KEY] == Keys.GEAR_TYPE_BIKE):
                    tags.append(gear[Keys.GEAR_NAME_KEY])
        return tags

    def create_activity_tag(self, activity_id, tag):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        if tag is None or len(tag) == 0:
            raise Exception("Bad parameter.")
        return self.database.create_tag(activity_id, tag)

    def retrieve_activity_tags(self, activity_id):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_tags(activity_id)

    def create_tags_on_activity(self, activity, tags):
        """Adds tags to an activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity is None:
            raise Exception("Bad parameter.")
        if tags is None:
            raise Exception("Bad parameter.")
        return self.database.create_tags_on_activity(activity, tags)

    def create_default_tags_on_activity(self, user_id, activity_type, activity_id):
        """Adds tags to an activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("Bad parameter.")

        defaults = self.retrieve_gear_defaults(user_id)
        for default in defaults:
            if default[Keys.ACTIVITY_TYPE_KEY] == activity_type:
                tags = []
                tags.append(default[Keys.GEAR_NAME_KEY])
                return self.database.create_tags_on_activity_by_id(activity_id, tags)
        return False

    @staticmethod
    def distance_for_activity(activity):
        if Keys.APP_DISTANCE_KEY in activity:
            return activity[Keys.APP_DISTANCE_KEY]
        if Keys.ACTIVITY_SUMMARY_KEY in activity:
            summary_data = activity[Keys.ACTIVITY_SUMMARY_KEY]
            if Keys.LONGEST_DISTANCE in summary_data:
                return summary_data[Keys.LONGEST_DISTANCE]
        return 0.0

    @staticmethod
    def distance_for_tag_cb(tag_distances, activity, user_id):
        if tag_distances is None:
            return
        if activity is None:
            return

        # Load tags associated with this activity.
        activity_tags = None
        if Keys.ACTIVITY_TAGS_KEY in activity:
            activity_tags = activity[Keys.ACTIVITY_TAGS_KEY]

        # No sense in proceeding if this activity does not have any tags.
        if activity_tags is None:
            return

        # Retrieve distance for this activity.
        distance = DataMgr.distance_for_activity(activity)

        for distance_tag in tag_distances.keys():
            if distance_tag in activity_tags:
                tag_distances[distance_tag] = tag_distances[distance_tag] + distance

    def distance_for_tags(self, user_id, tags):
        """Computes the distance (in meters) for activities with the combination of user and tag."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if tags is None:
            raise Exception("Bad parameter.")

        # Initialize.
        tag_distances = {}
        for tag in tags:
            tag_distances[tag] = 0.0

        self.retrieve_each_user_activity(tag_distances, user_id, DataMgr.distance_for_tag_cb)
        return tag_distances

    def create_activity_comment(self, activity_id, commenter_id, comment):
        """Create method for a comment on an activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("Bad parameter.")
        if commenter_id is None:
            raise Exception("Bad parameter.")
        if comment is None or len(comment) == 0:
            raise Exception("Bad parameter.")
        return self.database.create_activity_comment(activity_id, commenter_id, comment)

    def retrieve_activity_comments(self, activity_id):
        """Returns a list containing all of the comments on the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_comments(activity_id)

    def store_user_estimated_ftp(self, user_id, estimated_ftp):
        """Creates or updates the user's estimated FTP in the database."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if estimated_ftp is None:
            raise Exception("Bad parameter.")
        return self.database.update_user_setting(user_id, Keys.ESTIMATED_FTP_KEY, estimated_ftp)

    def retrieve_user_estimated_ftp(self, user_id):
        """Retrieves the user's estimated FTP in the database."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user_setting(user_id, Keys.ESTIMATED_FTP_KEY)

    def retrieve_user_goal(self, user_id):
        """Retrieves the user's current goal."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        goal = self.database.retrieve_user_setting(user_id, Keys.GOAL_KEY)
        goal_date_str = self.database.retrieve_user_setting(user_id, Keys.GOAL_DATE_KEY)
        if goal_date_str is not None:
            goal_date = int(goal_date_str)
        else:
            goal_date = None
        return goal, goal_date

    def update_activity_bests_and_personal_records(self, user_id, activity_id, activity_type, activity_time, bests):
        """Update method for a user's personal records. Caches the bests from the given activity and updates"""
        """the personal record cache, if appropriate."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if activity_id is None:
            raise Exception("Bad parameter.")
        if activity_type is None:
            raise Exception("Bad parameter.")
        if activity_time is None:
            raise Exception("Bad parameter.")
        if bests is None:
            raise Exception("Bad parameter.")

        # This object will keep track of the personal records.
        summarizer = Summarizer.Summarizer()

        # Load existing personal records from the PR cache.
        all_personal_records = self.database.retrieve_user_personal_records(user_id)
        for record_activity_type in all_personal_records.keys():
            summarizer.set_record_dictionary(record_activity_type, all_personal_records[record_activity_type])
        do_update = len(all_personal_records) > 0

        # Add data from the new activity.
        summarizer.add_activity_data(activity_id, activity_type, activity_time, bests)
 
        # Create or update the personal records cache.
        all_personal_records[activity_type] = summarizer.get_record_dictionary(activity_type)
        if do_update:
            self.database.update_user_personal_records(user_id, all_personal_records)
        else:
            self.database.create_user_personal_records(user_id, all_personal_records)

        # Cache the summary data from this activity so we don't have to recompute everything again.
        return self.database.create_activity_bests(user_id, activity_id, activity_type, activity_time, bests)

    def retrieve_user_personal_records(self, user_id):
        """Retrieve method for a user's personal record."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user_personal_records(user_id)

    def delete_all_user_personal_records(self, user_id):
        """Delete method for a user's personal record."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_all_user_personal_records(user_id)

    def refresh_user_personal_records(self, user_id):
        """Delete method for a user's personal record."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        # This object will keep track of the personal records.
        summarizer = Summarizer.Summarizer()

        # Load existing personal records from the PR cache.
        activity_bests = self.database.retrieve_activity_bests_for_user(user_id)
        for activity_id in activity_bests.keys():
            bests = activity_bests[activity_id]
            if Keys.APP_TYPE_KEY in bests:
                activity_type = bests[Keys.APP_TYPE_KEY]

        # TODO
        return True

    def create_workout(self, user_id, workout_obj):
        """Create method for a workout."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if workout_obj is None:
            raise Exception("Bad parameter.")
        return self.database.create_workout(user_id, workout_obj)

    def retrieve_workout(self, user_id, workout_id):
        """Retrieve method for the workout with the specified user and ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_workout(user_id, workout_id)

    def retrieve_workouts_for_user(self, user_id):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_workouts_for_user(user_id)

    def retrieve_workouts_calendar_id_for_user(self, user_id):
        """Retrieve method for the ical calendar ID for with specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_workouts_calendar_id_for_user(user_id)

    def retrieve_workouts_by_calendar_id(self, calendar_id):
        """Retrieve method for all workouts pertaining to the calendar with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if calendar_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_workouts_by_calendar_id(calendar_id)

    def delete_workouts_for_date_range(self, user_id, start_time, end_time):
        """Delete method for all workouts pertaining for the specified user within the given date range."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        new_workouts_list = []
        old_workouts_list = self.database.retrieve_workouts_for_user(user_id)
        for workout in old_workouts_list:
            if workout.scheduled_time is not None and (workout.scheduled_time < start_time or workout.scheduled_time > end_time):
                new_workouts_list.append(workout)
        return self.database.update_workouts_for_user(user_id, new_workouts_list)

    def delete_workout(self, user_id, workout_id):
        """Delete method for the workout with the specified ID and belonging to the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if workout_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_workout(user_id, workout_id)

    def retrieve_users_without_scheduled_workouts(self):
        """Returns a list of user IDs for users who have workout plans that need to be re-run."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.retrieve_users_without_scheduled_workouts()

    def create_gear(self, user_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Create method for gear."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_type is None:
            raise Exception("Bad parameter.")
        if gear_name is None:
            raise Exception("Bad parameter.")
        if gear_description is None:
            raise Exception("Bad parameter.")

        gear_id = uuid.uuid4()
        return self.database.create_gear(user_id, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time)

    def retrieve_gear(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_gear(user_id)

    def retrieve_gear_of_specified_type_for_user(self, user_id, gear_type):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_type is None:
            raise Exception("Bad parameter.")

        final_gear_list = []
        gear_list = self.database.retrieve_gear(user_id)
        for gear in gear_list:
            if Keys.GEAR_TYPE_KEY in gear:
                if gear_type == gear[Keys.GEAR_TYPE_KEY]:
                    final_gear_list.append(gear)
        return final_gear_list

    def update_gear(self, user_id, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        return self.database.update_gear(user_id, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time)

    def delete_gear(self, user_id, gear_id):
        """Delete method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_gear(user_id, gear_id)

    def retrieve_gear_defaults(self, user_id):
        """Retrieve method for the gear that is, by default, associated with each activity type. Result is a JSON string."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_gear_defaults(user_id)

    def update_gear_defaults(self, user_id, activity_type, gear_name):
        """Retrieve method for the gear that is, by default, associated with each activity type. Result is a JSON string."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if activity_type is None:
            raise Exception("Bad parameter.")
        if gear_name is None:
            raise Exception("Bad parameter.")

        user_gear = self.retrieve_gear(user_id)
        found = False
        for gear in user_gear:
            if Keys.GEAR_NAME_KEY in gear and gear[Keys.GEAR_NAME_KEY] == gear_name:
                found = True
                break
        if not found:
            raise Exception("Invalid gear name.")
        return self.database.update_gear_defaults(user_id, activity_type, gear_name)

    def create_service_record(self, user_id, gear_id, record_date, record_description):
        """Create method for gear service records."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        if record_date is None:
            raise Exception("Bad parameter.")
        if record_description is None:
            raise Exception("Bad parameter.")
        service_record_id = uuid.uuid4()
        return self.database.create_service_record(user_id, gear_id, service_record_id, record_date, record_description)

    def delete_service_record(self, user_id, gear_id, service_record_id):
        """Delete method for gear service records."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        if service_record_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_service_record(user_id, gear_id, service_record_id)

    def generate_workout_plan_for_user(self, user_id):
        """Generates/updates a workout plan for the user with the specified ID."""
        if self.workout_plan_gen_scheduler is None:
            raise Exception("No workout scheduler.")
        if user_id is None:
            raise Exception("Bad parameter.")
        self.workout_plan_gen_scheduler.add_user_to_queue(user_id, self)

    def generate_workout_plan_from_inputs(self, inputs):
        """Generates a workout plan from the specified inputs."""
        if self.workout_plan_gen_scheduler is None:
            raise Exception("No workout scheduler.")
        if inputs is None:
            raise Exception("Bad parameter.")
        self.workout_plan_gen_scheduler.add_inputs_to_queue(inputs, self)

    def merge_gpx_files(self, user_id, uploaded_file1_data, uploaded_file2_data):
        if user_id is None:
            raise Exception("Bad parameter.")
        if uploaded_file1_data is None:
            raise Exception("Bad parameter.")
        if uploaded_file2_data is None:
            raise Exception("Bad parameter.")

        merge_tool = GpxMerge.GpxMerge()

    def get_location_description(self, activity_id):
        """Returns the political location that corresponds to an activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("Bad parameter.")

        if self.map_search is None:
            self.map_search = MapSearch.MapSearch(self.root_url + '/data/world.geo.json', self.root_url + '/data/us_states.geo.json', self.root_url + '/data/canada.geo.json')
        if self.map_search is None:
            raise Exception("Internal error.")

        location_description = []
        locations = self.retrieve_activity_locations(activity_id)
        if locations and len(locations) > 0:
            first_loc = locations[0]
            location_description = self.map_search.search_map(float(first_loc[Keys.LOCATION_LAT_KEY]), float(first_loc[Keys.LOCATION_LON_KEY]))
        return location_description

    def compute_location_heat_map(self, activities):
        """Returns a count of the number of times activities have been performed in each location."""
        if self.database is None:
            raise Exception("No database.")
        if activities is None:
            raise Exception("Bad parameter.")

        heat_map = {}

        for activity in activities:
            if Keys.ACTIVITY_ID_KEY in activity and activity[Keys.ACTIVITY_ID_KEY]:
                summary_data = self.retrieve_activity_summary(activity[Keys.ACTIVITY_ID_KEY])
                if summary_data is not None and Keys.ACTIVITY_LOCATION_DESCRIPTION_KEY in summary_data:
                    locations = summary_data[Keys.ACTIVITY_LOCATION_DESCRIPTION_KEY]
                    locations_str = ""
                    for location_elem in reversed(locations):
                        if len(locations_str) > 0:
                            locations_str += ", "
                        locations_str += location_elem
                    if locations_str in heat_map:
                        heat_map[locations_str] = heat_map[locations_str] + 1
                    else:
                        heat_map[locations_str] = 1
        return heat_map

    def retrieve_recent_bests(self, user_id, timeframe):
        """Return a dictionary of all best performances in the specified time frame."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        summarizer = Summarizer.Summarizer()

        # We're only interested in activities from this time forward.
        if timeframe is None:
            cutoff_time = None
        else:
            cutoff_time = time.time() - timeframe

        # Load cached summary data from all previous activities.
        all_activity_bests = self.database.retrieve_recent_activity_bests_for_user(user_id, cutoff_time)
        if all_activity_bests is not None:
            for activity_id in all_activity_bests:
                activity_bests = all_activity_bests[activity_id]
                summarizer.add_activity_data(activity_id, activity_bests[Keys.ACTIVITY_TYPE_KEY], activity_bests[Keys.ACTIVITY_START_TIME_KEY], activity_bests)

        # Output is a dictionary for each sport type.
        cycling_bests = summarizer.get_record_dictionary(Keys.TYPE_CYCLING_KEY)
        running_bests = summarizer.get_record_dictionary(Keys.TYPE_RUNNING_KEY)
        cycling_summary = summarizer.get_summary_dictionary(Keys.TYPE_CYCLING_KEY)
        running_summary = summarizer.get_summary_dictionary(Keys.TYPE_RUNNING_KEY)
        return cycling_bests, running_bests, cycling_summary, running_summary

    def retrieve_bounded_activity_bests_for_user(self, user_id, cutoff_time_lower, cutoff_time_higher):
        """Return a dictionary of all best performances in the specified time frame."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        summarizer = Summarizer.Summarizer()

        # Load cached summary data from all previous activities.
        all_activity_bests = self.database.retrieve_bounded_activity_bests_for_user(user_id, cutoff_time_lower, cutoff_time_higher)
        if all_activity_bests is not None:
            for activity_id in all_activity_bests:
                activity_bests = all_activity_bests[activity_id]
                summarizer.add_activity_data(activity_id, activity_bests[Keys.ACTIVITY_TYPE_KEY], activity_bests[Keys.ACTIVITY_START_TIME_KEY], activity_bests)

        # Output is a dictionary for each sport type.
        cycling_bests = summarizer.get_record_dictionary(Keys.TYPE_CYCLING_KEY)
        running_bests = summarizer.get_record_dictionary(Keys.TYPE_RUNNING_KEY)
        cycling_summary = summarizer.get_summary_dictionary(Keys.TYPE_CYCLING_KEY)
        running_summary = summarizer.get_summary_dictionary(Keys.TYPE_RUNNING_KEY)
        return cycling_bests, running_bests, cycling_summary, running_summary

    def retrieve_bests_for_activity_type(self, user_id, activity_type, key):
        """Return a sorted list of all records for the given activity type and key."""
        def compare(a, b):
            if a[0] > b[0]:
                return 1
            elif a[0] == b[0]:
                return 0
            else:
                return -1

        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if activity_type is None:
            raise Exception("Bad parameter.")
        if key is None:
            raise Exception("Bad parameter.")

        bests = []

        # Load cached summary data from all previous activities.
        all_activity_bests = self.database.retrieve_recent_activity_bests_for_user(user_id, None)
        if all_activity_bests is not None:
            for activity_id in all_activity_bests:
                activity_bests = all_activity_bests[activity_id]
                if (Keys.ACTIVITY_TYPE_KEY in activity_bests) and (activity_bests[Keys.ACTIVITY_TYPE_KEY] == activity_type) and (key in activity_bests):
                    record = []
                    record.append(activity_bests[key])
                    record.append(activity_id)
                    bests.append(record)

        bests.sort(compare)
        return bests

    def analyze_unanalyzed_activities(self, user_id, timeframe):
        """Looks through the user's activities (within the given timeframe) and schedules any unanalyzed ones for analysis."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        # We're only interested in activities from this time forward.
        if timeframe is None:
            cutoff_time = None
        else:
            cutoff_time = time.time() - timeframe

        num_unanalyzed = 0

        all_activities = self.retrieve_user_activity_list(user_id, None, None, None)
        all_activity_bests = self.database.retrieve_recent_activity_bests_for_user(user_id, cutoff_time)

        for activity in all_activities:
            activity_id = activity[Keys.ACTIVITY_ID_KEY]
            if Keys.ACTIVITY_START_TIME_KEY in activity:
                activity_time = activity[Keys.ACTIVITY_START_TIME_KEY]
                if cutoff_time is None or activity_time > cutoff_time:
                    if activity_id not in all_activity_bests:
                        num_unanalyzed = num_unanalyzed + 1
                        complete_activity_data = self.retrieve_activity(activity_id)
                        self.analyze_activity(complete_activity_data, user_id)

        return num_unanalyzed

    def compute_progression(self, user_id, user_activities, activity_type, key):
        """Return a sorted list of all records for the given activity type and key."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if user_activities is None:
            raise Exception("Bad parameter.")
        if activity_type is None:
            raise Exception("Bad parameter.")
        if key is None:
            raise Exception("Bad parameter.")

        bests = []

        # Load cached summary data from all previous activities.
        all_activity_bests = self.database.retrieve_recent_activity_bests_for_user(user_id, None)
        if all_activity_bests is not None:
            best_value = None
    
            # Loop through each of the user's activities, the key is the activity ID.
            for activity in user_activities:
                if Keys.ACTIVITY_ID_KEY in activity:
                    activity_id = activity[Keys.ACTIVITY_ID_KEY]

                    # Check the list of bests for the activity ID.
                    if activity_id in all_activity_bests:
                        activity_bests = all_activity_bests[activity_id]
                        if (Keys.ACTIVITY_TYPE_KEY in activity_bests) and (activity_bests[Keys.ACTIVITY_TYPE_KEY] == activity_type) and (key in activity_bests):
                            current_value = activity_bests[key]
                            if best_value is None or Summarizer.Summarizer.is_better(key, best_value, current_value):
                                record = []
                                record.append(current_value)
                                record.append(activity_id)
                                bests.append(record)
                                best_value = current_value

        return bests

    def compute_run_training_paces(self, user_id, running_bests):
        """Computes the user's run training paces by searching the list of running 'bests' for the fastest 5K."""
        run_paces = {}
        if Keys.BEST_5K in running_bests:
            best_time_secs = running_bests[Keys.BEST_5K]
            best_time_mins = best_time_secs[0] / 60
            calc = TrainingPaceCalculator.TrainingPaceCalculator()
            run_paces = calc.calc_from_race_distance_in_meters(5000, best_time_mins)
        return run_paces

    def compute_power_zone_distribution(self, ftp, powers):
        """Takes the list of power readings and determines how many belong in each power zone, based on the user's FTP."""
        calc = FtpCalculator.FtpCalculator()
        return calc.compute_power_zone_distribution(ftp, powers)

    def retrieve_heart_rate_zones(self, max_hr):
        """Returns an array containing the maximum heart rate for each training zone."""
        calc = HeartRateCalculator.HeartRateCalculator()
        return calc.training_zones(max_hr)

    def retrieve_power_training_zones(self, ftp):
        """Returns an array containing the maximum power rate for each training zone."""
        calc = FtpCalculator.FtpCalculator()
        return calc.power_training_zones(ftp)

    def retrieve_activity_types(self):
        """Returns a the list of activity types that the software understands."""
        all_activity_types = []
        all_activity_types.extend(Keys.FOOT_BASED_ACTIVITIES)
        all_activity_types.extend(Keys.CYCLING_ACTIVITIES)
        all_activity_types.extend(Keys.SWIMMING_ACTIVITIES)
        all_activity_types.extend(Keys.STRENGTH_ACTIVITIES)
        all_activity_types.append(Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY)
        return all_activity_types

    def estimate_vo2_max(self, resting_hr, max_hr):
        """Estimates VO2 Max, based on resting and max heart rates."""
        calc = VO2MaxCalculator.VO2MaxCalculator()
        estimated_vo2_max = calc.estimate_vo2max_from_heart_rate(resting_hr, max_hr)
        return estimated_vo2_max

    def estimate_bmi(self, weight_metric, height_metric):
        """Estimates BMI."""
        calc = BmiCalculator.BmiCalculator()
        bmi = calc.estimate_bmi(weight_metric, height_metric)
        return bmi
