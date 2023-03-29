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

import base64
import datetime
import hashlib
import os
import threading
import time
import uuid
import AppDatabase
import BmiCalculator
import FtpCalculator
import HeartRateCalculator
import Importer
import InputChecker
import Keys
import MapSearch
import MergeTool
import Summarizer
import TrainingPaceCalculator
import Units
import VO2MaxCalculator
import celery

SIX_MONTHS = ((365.25 / 2.0) * 24.0 * 60.0 * 60.0)
ONE_YEAR = (365.25 * 24.0 * 60.0 * 60.0)
ONE_WEEK = (7.0 * 24.0 * 60.0 * 60.0)
FOUR_WEEKS = (28.0 * 24.0 * 60.0 * 60.0)
EIGHT_WEEKS = (56.0 * 24.0 * 60.0 * 60.0)

g_api_key_rate_lock = threading.Lock()
g_api_key_rates = {}
g_last_api_reset = 0 # Timestamp of when g_api_key_rates was last cleared 

def get_activities_sort_key(item):
    # Was the start time provided? If not, look at the first location.
    if Keys.ACTIVITY_START_TIME_KEY in item:
        return item[Keys.ACTIVITY_START_TIME_KEY]
    return 0

class DataMgr(Importer.ActivityWriter):
    """Data store abstraction"""

    def __init__(self, *, config, root_url, analysis_scheduler, import_scheduler):
        """Constructor"""
        assert config is not None
        self.config = config
        self.root_url = root_url
        self.analysis_scheduler = analysis_scheduler
        self.import_scheduler = import_scheduler
        self.database = AppDatabase.MongoDatabase()
        self.database.connect(config)
        self.map_search = None
        self.celery_worker = celery.Celery(Keys.CELERY_PROJECT_NAME)
        self.celery_worker.config_from_object('CeleryConfig')
        if config is not None:
            self.celery_worker.conf.broker_url = config.get_broker_url()
        super(Importer.ActivityWriter, self).__init__()

    def terminate(self):
        """Destructor"""
        self.analysis_scheduler = None
        self.import_scheduler = None
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

    def schedule_activity_analysis(self, activity, activity_user_id):
        """Schedules the specified activity for analysis."""
        if activity is None:
            raise Exception("No activity object.")
        if activity_user_id is None:
            raise Exception("No activity user ID.")
        if not InputChecker.is_hex_str(activity_user_id):
            raise Exception("Invalid activity user ID.")
        if self.analysis_scheduler is None:
            raise Exception("No analysis scheduler.")

        activity[Keys.ACTIVITY_USER_ID_KEY] = activity_user_id
        task_id, internal_task_id = self.analysis_scheduler.add_activity_to_analysis_queue(activity)
        if [task_id, internal_task_id].count(None) == 0:
            self.create_deferred_task(activity_user_id, Keys.ANALYSIS_TASK_KEY, task_id, internal_task_id, None)

    def analyze_activity_by_id(self, activity_id, activity_user_id):
        """Schedules the specified activity for analysis."""
        if activity_id is None:
            raise Exception("No activity ID.")
        if activity_user_id is None:
            raise Exception("No activity user ID.")

        complete_activity_data = self.retrieve_activity(activity_id)
        self.schedule_activity_analysis(complete_activity_data, activity_user_id)

    def schedule_personal_records_refresh(self, user_id):
        """Schedules the specified activity for analysis."""
        if user_id is None:
            raise Exception("No user ID.")
        if self.analysis_scheduler is None:
            raise Exception("No analysis scheduler.")

        task_id, internal_task_id = self.analysis_scheduler.add_personal_records_analysis_to_queue(user_id)
        if [task_id, internal_task_id].count(None) == 0:
            self.create_deferred_task(user_id, Keys.ANALYSIS_TASK_KEY, task_id, internal_task_id, None)

    def compute_activity_end_time_ms(self, activity):
        """Examines the activity and computes the time at which the activity ended."""
        end_time_ms = None

        # Look through activity attributes that have a "time".
        search_keys = []
        search_keys.append(Keys.APP_LOCATIONS_KEY)
        search_keys.append(Keys.APP_ACCELEROMETER_KEY)
        for search_key in search_keys:

            # Read the last item out of the list since they should be in chronological order.
            if search_key in activity and isinstance(activity[search_key], list) and len(activity[search_key]) > 0:
                last_list_entry = (activity[search_key])[-1]
                if "time" in last_list_entry:
                    possible_end_time_ms = last_list_entry["time"]
                    if end_time_ms is None or possible_end_time_ms > end_time_ms:
                        end_time_ms = possible_end_time_ms

        return end_time_ms

    def update_activity_end_time_secs(self, activity, end_time_sec):
        """Utility function for updating the activity's ending time in the database."""
        if self.database is None:
            raise Exception("No database.")
        if activity is None:
            raise Exception("No activity object.")
        if end_time_sec is None:
            raise Exception("End time not provided.")
        return self.database.create_or_update_activity_metadata(activity[Keys.ACTIVITY_ID_KEY], None, Keys.ACTIVITY_END_TIME_KEY, int(end_time_sec), False)

    def compute_and_store_activity_end_time(self, activity):
        """Examines the activity and computes the time at which the activity ended, storing it so we don't have to do this again."""
        if self.database is None:
            raise Exception("No database.")

        end_time_sec = None

        # Compute from the activity's raw data.
        end_time_ms = self.compute_activity_end_time_ms(activity)
        if end_time_ms is not None:
            end_time_sec = end_time_ms / 1000

        # If we couldn't find anything with a time then just duplicate the start time, assuming it's a manually entered workout or something.
        if end_time_sec is None:
            end_time_sec = activity[Keys.ACTIVITY_START_TIME_KEY]

        # Store the ending time, so we don't have to go through this again.
        if end_time_sec is not None:
            self.update_activity_end_time_secs(activity, end_time_sec)

        return end_time_sec

    def get_activity_start_and_end_times(self, activity):
        """Retrieves the start time and end time, computing the ending time, if necessary."""
        if activity is None:
            raise Exception("No activity object.")

        activity_start_time_sec = activity[Keys.ACTIVITY_START_TIME_KEY]
        if Keys.ACTIVITY_END_TIME_KEY not in activity:
            activity_end_time_sec = self.compute_and_store_activity_end_time(activity)
        else:
            activity_end_time_sec = activity[Keys.ACTIVITY_END_TIME_KEY]
        return activity_start_time_sec, activity_end_time_sec

    def is_duplicate_activity(self, user_id, start_time_sec, optional_activity_id):
        """Inherited from ActivityWriter. Returns TRUE if the activity appears to be a duplicate of another activity. Returns FALSE otherwise."""
        if self.database is None:
            raise Exception("No database.")

        # If an activity ID was specified then do any documents already exist with this ID?
        if optional_activity_id is not None:
            if self.database.retrieve_activity(optional_activity_id) is not None:
                return True

        # Look through the user's activities for ones that overlap with the given start time.
        activities = self.database.retrieve_user_activity_list(user_id, None, None, True)
        for activity in activities:

            if Keys.ACTIVITY_START_TIME_KEY in activity:

                # Get the activity start and end times.
                activity_start_time_sec, activity_end_time_sec = self.get_activity_start_and_end_times(activity)

                # We're looking for activities that start within the bounds of another activity.
                if start_time_sec >= activity_start_time_sec and start_time_sec < activity_end_time_sec:
                    return True

        return False

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time, desired_activity_id):
        """Inherited from ActivityWriter. Called when we start reading an activity file."""
        if self.database is None:
            raise Exception("No database.")

        # Device is unknown.
        device_str = ""

        # Create the device ID, or use the provided one.
        if desired_activity_id is None:
            activity_id = self.create_activity_id()
        else:
            activity_id = desired_activity_id

        # Add the activity to the database.
        if stream_name is None:
            stream_name = ""
        if not self.database.create_activity(activity_id, stream_name, start_time, device_str):
            return None, None
        if activity_type is not None and len(activity_type) > 0:
            self.database.create_or_update_activity_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, activity_type, False)
            self.create_default_tags_on_activity(user_id, activity_type, activity_id)

        # If given a user ID then associate the activity with the user.
        if user_id is not None:
            self.database.create_or_update_activity_metadata(activity_id, 0, Keys.ACTIVITY_USER_ID_KEY, user_id, False)
        return device_str, activity_id

    def create_activity_track(self, device_str, activity_id, track_name, track_description):
        """Inherited from ActivityWriter."""
        pass

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
        if date_time is None:
            raise Exception("No timestamp.")
        if key is None:
            raise Exception("No key.")
        if value is None:
            raise Exception("No value.")
        if create_list is None:
            raise Exception("Missing parameter.")
        return self.database.create_or_update_activity_metadata(activity_id, date_time, key, value, create_list)

    def create_activity_metadata_list(self, activity_id, key, values):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        if key is None:
            raise Exception("No key.")
        if values is None:
            raise Exception("No values.")
        return self.database.create_or_update_activity_metadata_list(activity_id, key, values)

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

    def finish_activity(self, activity_id, end_time_ms):
        """Inherited from ActivityWriter. Called for post-processing."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_or_update_activity_metadata(activity_id, int(end_time_ms), Keys.ACTIVITY_END_TIME_KEY, int(end_time_ms / 1000), False)

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

    def update_deferred_task(self, user_id, internal_task_id, activity_id, status):
        """Returns a list of all incomplete tasks."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("No user ID.")
        if internal_task_id is None:
            raise Exception("No internal task ID.")
        if status is None:
            raise Exception("No status.")
        return self.database.update_deferred_task(user_id, internal_task_id, activity_id, status)

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

    def import_activity_from_file(self, username, user_id, uploaded_file_data, uploaded_file_name, desired_activity_id):
        """Imports the contents of a local file into the database. Desired activity ID is optional."""
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

        return self.import_scheduler.add_file_to_queue(username, user_id, uploaded_file_data, uploaded_file_name, desired_activity_id, self)

    def get_user_photos_dir(self, user_id):
        """Calculates the photos dir assigned to the specified user and creates if it does not exist."""

        # Where are we storing photos?
        photos_dir = self.config.get_photos_dir()
        if len(photos_dir) == 0:
            raise Exception("No photos directory.")

        # Create the directory, if it does not already exist.
        user_photos_dir = os.path.join(os.path.normpath(os.path.expanduser(photos_dir)), str(user_id))
        if not os.path.exists(user_photos_dir):
            os.makedirs(user_photos_dir)

        # Sanity check.
        if not os.path.exists(user_photos_dir):
            raise Exception("Photos directory not created.")
        return user_photos_dir

    def attach_photo_to_activity(self, user_id, uploaded_file_data, activity_id):
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

        # Decode the uplaoded data.
        uploaded_file_data = uploaded_file_data.replace(" ", "+") # Some JS base64 encoders replace plus with space, so we need to undo that.
        decoded_file_data = base64.b64decode(uploaded_file_data)

        # Check the file size.
        if len(decoded_file_data) > self.config.get_photos_max_file_size():
            raise Exception("The file is too large.")

        # Hash the photo. This will prevent duplicates as well as give us a unique name.
        h = hashlib.sha512()
        h.update(str(decoded_file_data).encode('utf-8'))
        hash_str = h.hexdigest()

        # Where are we storing photos?
        user_photos_dir = self.get_user_photos_dir(user_id)

        # Save the file to the user's photos directory.
        try:
            local_file_name = os.path.join(user_photos_dir, hash_str)
            if not os.path.isfile(local_file_name):
                with open(local_file_name, 'wb') as local_file:
                    local_file.write(decoded_file_data)
        except:
            raise Exception("Could not save the photo.")

        # Attach the hash to the activity.
        return self.database.create_activity_photo(user_id, activity_id, hash_str)

    def list_activity_photos(self, activity_id):
        """Lists all photos associated with an activity. Response is a list of identifiers."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")

        activity = self.database.retrieve_activity_small(activity_id)
        if activity is not None and Keys.ACTIVITY_PHOTOS_KEY in activity:
            return activity[Keys.ACTIVITY_PHOTOS_KEY]
        return None

    def delete_activity_photo(self, activity_id, photo_id):
        """Lists all photos associated with an activity. Response is a list of identifiers."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        if photo_id is None:
            raise Exception("No photo ID.")
        return self.database.delete_activity_photo(activity_id, photo_id)

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
        if device_str is None:
            raise Exception("Bad parameter.")
        if activity_id is None:
            raise Exception("Bad parameter.")
        return self.database.update_activity(device_str, activity_id, locations, sensor_readings_dict, metadata_list_dict)

    def is_activity_public(self, activity):
        """Helper function for returning whether or not an activity is publically visible."""
        if Keys.ACTIVITY_VISIBILITY_KEY in activity:
            if activity[Keys.ACTIVITY_VISIBILITY_KEY] == "private":
                return False
        return True

    def is_activity_id_public(self, activity_id):
        """Helper function for returning whether or not an activity is publically visible."""
        if activity_id is None:
            raise Exception("Bad parameter.")

        visibility = self.retrieve_activity_visibility(activity_id)
        if visibility is not None:
            if visibility == "private":
                return False
        return True

    def retrieve_user_activity_list(self, user_id, user_realname, start_time, end_time, num_results):
        """Returns a list containing all of the user's activities, up to num_results. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        activities = []

        # List activities recorded on devices registered to the user.
        devices = self.database.retrieve_user_devices(user_id)
        if devices is not None:
            devices = list(set(devices)) # De-duplicate
            device_activities = self.database.retrieve_devices_activity_list(devices, start_time, end_time, False)
            if device_activities is not None:
                for device_activity in device_activities:
                    device_activity[Keys.REALNAME_KEY] = user_realname
                    self.update_activity_start_time(device_activity)
                activities.extend(device_activities)

        # List activities with no device that are associated with the user.
        user_activities = self.database.retrieve_user_activity_list(user_id, start_time, end_time, False)
        if user_activities is not None:
            for user_activity in user_activities:
                user_activity[Keys.REALNAME_KEY] = user_realname
            activities.extend(user_activities)

        # Sort and limit the list.
        if len(activities) > 0:
            activities = sorted(activities, key=get_activities_sort_key, reverse=True)[:num_results]

        return activities

    def retrieve_each_user_activity(self, user_id, context, cb_func, start_time, end_time, return_all_data):
        """Fires a callback for all of the user's activities. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if context is None:
            raise Exception("Bad parameter.")
        if cb_func is None:
            raise Exception("Bad parameter.")
        if return_all_data is None:
            raise Exception("Bad parameter.")

        # List activities recorded on devices registered to the user.
        devices = self.database.retrieve_user_devices(user_id)
        if devices is not None:
            devices = list(set(devices)) # De-duplicate
            if devices is not None:
                for device in devices:
                    self.database.retrieve_each_device_activity(user_id, device, context, cb_func, start_time, end_time, return_all_data)

        # List activities with no device that are associated with the user.
        return self.database.retrieve_each_user_activity(user_id, context, cb_func, start_time, end_time, return_all_data)

    def retrieve_all_activities_visible_to_user(self, user_id, user_realname, start_time, end_time, num_results):
        """Returns a list containing all of the activities visible to the specified user, up to num_results. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        # Start with the user's own activities.
        activities = self.retrieve_user_activity_list(user_id, user_realname, start_time, end_time, num_results)

        # Add the activities of users they follow.
        friends = self.database.retrieve_friends(user_id)
        for friend in friends:
            more_activities = self.retrieve_user_activity_list(friend[Keys.DATABASE_ID_KEY], friend[Keys.REALNAME_KEY], start_time, end_time, num_results)
            for another_activity in more_activities:
                if self.is_activity_public(another_activity):
                    activities.append(another_activity)

        # Sort and limit the list.
        if len(activities) > 0:
            activities = sorted(activities, key=get_activities_sort_key, reverse=True)[:num_results]

        return activities

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

    def delete_activity(self, user_id, activity_id):
        """Delete the activity with the specified object ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if activity_id is None:
            raise Exception("Bad parameter.")

        # Delete the activity as well as the cache of the PRs performed during that activity.
        result = self.database.delete_activity(activity_id)

        if result:

            # Delete the activity bests (there might not be any), so don't bother checking the return code.
            self.database.delete_activity_best_for_user(user_id, activity_id)

            # Delete the uploaded file (if any).
            self.database.delete_uploaded_file(activity_id)

            # Recreate the user's all-time PR list as the previous one could have contained data from the now deleted activity.
            result = self.schedule_personal_records_refresh(user_id)

        return result

    def trim_activity(self, activity, trim_from, num_seconds):
        if self.database is None:
            raise Exception("No database.")
        if activity is None:
            raise Exception("Bad parameter.")
        if trim_from is None:
            raise Exception("Bad parameter.")
        if num_seconds is None:
            raise Exception("Bad parameter.")

        # Make sure the ending time has been computed, compute it if it has not.
        trim_before_ms = 0
        trim_after_ms = self.compute_activity_end_time_ms(activity)
        if trim_after_ms is None:
            raise Exception("Cannot compute the ending time for the activity.")

        # Compute the new activity start and ending time.
        if trim_from == Keys.TRIM_FROM_BEGINNING_VALUE:
            if Keys.ACTIVITY_START_TIME_KEY in activity:
                trim_before_ms = activity[Keys.ACTIVITY_START_TIME_KEY] * 1000
                trim_before_ms = trim_before_ms + (num_seconds * 1000)
        if trim_from == Keys.TRIM_FROM_END_VALUE:
            trim_after_ms = trim_after_ms - (num_seconds * 1000)

        # Trim the location data.
        if Keys.APP_LOCATIONS_KEY in activity:
            old_locations = activity[Keys.APP_LOCATIONS_KEY]
            new_locations = []
            for location in old_locations:
                ts = location[Keys.LOCATION_TIME_KEY]
                if ts >= trim_before_ms and ts <= trim_after_ms:
                    new_locations.append(location)
            activity[Keys.APP_LOCATIONS_KEY] = new_locations

        # Trim the sensor data.
        for sensor_type in Keys.SENSOR_KEYS:
            if sensor_type in activity:
                try:
                    old_sensor_data = activity[sensor_type]
                    new_sensor_data = []

                    sensor_iter = iter(old_sensor_data)
                    sensor_reading = next(sensor_iter)
                    sensor_time = float(list(sensor_reading.keys())[0])

                    # Skip over everything before the start time.
                    while sensor_time < trim_before_ms:
                        sensor_reading = next(sensor_iter)
                        sensor_time = float(list(sensor_reading.keys())[0])

                    # Copy everything up the ending time.
                    while sensor_time < trim_after_ms:
                        sensor_reading = next(sensor_iter)
                        sensor_time = float(list(sensor_reading.keys())[0])
                        sensor_value = list(sensor_reading.values())[0]
                        new_sensor_data.append({str(sensor_time): sensor_value})
                except StopIteration:
                    pass

                activity[sensor_type] = new_sensor_data

        # Write the new, updated activity.
        self.database.recreate_activity(activity)

        # Activity will need to be reanalyzed.
        self.database.delete_activity_summary(activity[Keys.ACTIVITY_ID_KEY])

        return True

    def activity_exists(self, activity_id):
        """Determines whether or not there is a document corresonding to the activity ID."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("Bad parameter.")
        return self.database.activity_exists(activity_id)

    def retrieve_activity_visibility(self, activity_id):
        """Returns the visibility setting for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")

        activity = self.database.retrieve_activity_small(activity_id)
        if activity is not None and Keys.ACTIVITY_VISIBILITY_KEY in activity:
            return activity[Keys.ACTIVITY_VISIBILITY_KEY]
        return None

    def update_activity_visibility(self, activity_id, visibility):
        """Changes the visibility setting for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        if visibility is None:
            raise Exception("Bad parameter.")
        return self.database.create_or_update_activity_metadata(activity_id, None, Keys.ACTIVITY_VISIBILITY_KEY, visibility, False)

    def retrieve_activity_locations(self, activity_id):
        """Returns the location list for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_locations(activity_id)

    def delete_activity_sensor_readings(self, key, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if self.database is None:
            raise Exception("No database.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.delete_activity_sensor_readings(key, activity_id)

    def retrieve_most_recent_activity_id_for_device(self, device_str):
        """Returns the most recent activity id for the specified device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")

        activity = self.database.retrieve_most_recent_activity_for_device(device_str, False)
        if activity is None:
            return None
        return activity[Keys.ACTIVITY_ID_KEY]

    def retrieve_most_recent_activity_for_device(self, device_str):
        """Returns the most recent activity for the specified device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_most_recent_activity_for_device(device_str, False)

    def retrieve_most_recent_activity_for_user(self, user_devices):
        """Returns the most recent activity id for the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_devices is None:
            raise Exception("Bad parameter.")

        # Search through each device registered to the user.
        most_recent_activity = None
        for device_str in user_devices:

            # Find the most recent activity for the specified device.
            device_activity = self.retrieve_most_recent_activity_for_device(device_str)
            if device_activity is not None:

                # Is this more recent than our current most recent activity?
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

        activity = self.database.retrieve_activity_small(activity_id)
        if activity is not None and Keys.ACTIVITY_SUMMARY_KEY in activity:
            return activity[Keys.ACTIVITY_SUMMARY_KEY]
        return None

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

    def list_available_tags_for_activity_type_and_user(self, user_id, activity_type):
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
                    if gear[Keys.GEAR_RETIRE_TIME_KEY] == 0:
                        tags.append(gear[Keys.GEAR_NAME_KEY])
        return tags

    def retrieve_activity_tags(self, activity_id):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")

        activity = self.database.retrieve_activity_small(activity_id)
        if activity is not None and Keys.ACTIVITY_TAGS_KEY in activity:
            return activity[Keys.ACTIVITY_TAGS_KEY]
        return []

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
            if Keys.ACTIVITY_TYPE_KEY in default and default[Keys.ACTIVITY_TYPE_KEY] == activity_type:
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

        # Retrieve each activity, tag_distances will be updated in the callback.
        if not self.retrieve_each_user_activity(user_id, tag_distances, DataMgr.distance_for_tag_cb, None, None, False):
            raise Exception("Error retrieving activities.")
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

        activity = self.database.retrieve_activity_small(activity_id)
        if activity is not None and Keys.ACTIVITY_COMMENTS_KEY in activity:
            return activity[Keys.ACTIVITY_COMMENTS_KEY]
        return []

    def retrieve_user_goal(self, user_id):
        """Retrieves the goal distance and date that is used to suggest workouts."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        # Defaults.
        goal_distance = None
        goal_date = None
        goal_importance = None

        # Read the user's race calendar and find the next A race, or B race if an A race is not specified.
        # If no race is specified then return "Fitness" as a the goal with no specified date.
        now = time.time()
        user_races = self.database.retrieve_user_setting(user_id, Keys.USER_RACES)
        if user_races is not None:
            for race in user_races:

                # Only races that haven't happened yet.
                race_date = race[Keys.RACE_DATE_KEY]
                if race_date > now:

                    # Best goal not yet found, or the race is closer and equal or higher priority than the current best goal.
                    race_importance = race[Keys.RACE_IMPORTANCE_KEY]
                    if (goal_date is None) or (race_date < goal_date and race_importance <= goal_importance):
                        goal_distance = race[Keys.RACE_DISTANCE_KEY]
                        goal_date = race[Keys.RACE_DATE_KEY]
                        goal_importance = race[Keys.RACE_IMPORTANCE_KEY]

                    # This race is after the current best goal, but is longer.
                    if (race_date > goal_date) and (race_date <= goal_date + EIGHT_WEEKS) and (goal_distance > goal_distance):
                        goal_distance = race[Keys.RACE_DISTANCE_KEY]
                        goal_date = race[Keys.RACE_DATE_KEY]
                        goal_importance = race[Keys.RACE_IMPORTANCE_KEY]

        return goal_distance, goal_date

    def refresh_personal_records_cache(self, user_id):
        """Update method for a user's personal records. Caches the bests from the given activity and updates"""
        """the personal record cache, if appropriate."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        # This object will keep track of the personal records.
        summarizer = Summarizer.Summarizer()

        # Load existing activity bests into the summarizer.
        all_activity_bests = self.database.retrieve_activity_bests_for_user(user_id)

        # Cleanup the activity summary, removing any items that are no longer valid.
        old_activity_bests = {}
        for old_activity_id in all_activity_bests:
            if self.activity_exists(old_activity_id):

                # Activity still exists, add its data to the summary.
                old_activity_bests = all_activity_bests[old_activity_id]
                if Keys.ACTIVITY_TYPE_KEY in old_activity_bests and Keys.ACTIVITY_START_TIME_KEY in old_activity_bests:
                    old_activity_type = old_activity_bests[Keys.ACTIVITY_TYPE_KEY]
                    old_activity_time = old_activity_bests[Keys.ACTIVITY_START_TIME_KEY]
                    summarizer.add_activity_data(old_activity_id, old_activity_type, old_activity_time, old_activity_bests)
            else:

                # Activity no longer exists, remove it's summary from the database.
                self.database.delete_activity_best_for_user(user_id, old_activity_id)

        # Look for activities that haven't been analyzed at all.
        now = time.time()
        _ = self.analyze_unanalyzed_activities(user_id, now - SIX_MONTHS, now)

        # Create or update the personal records cache.
        if len(old_activity_bests) > 0:
            return self.database.update_user_personal_records(user_id, summarizer.bests)
        else:
            return self.database.create_user_personal_records(user_id, summarizer.bests)

    def update_activity_bests_and_personal_records_cache(self, user_id, activity_id, activity_type, activity_time, activity_bests, prune_activity_summary_cache):
        """Update method for a user's personal records. Caches the bests from the given activity and updates"""
        """the personal record cache, if appropriate."""
        """Checking that each activity summary is still valid is expensive, so the option to skip that step is provided via prune_activity_summary_cache."""
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
        if activity_bests is None:
            raise Exception("Bad parameter.")

        # This object will keep track of the personal records.
        summarizer = Summarizer.Summarizer()

        # Load existing activity bests into the summarizer.
        all_activity_bests = self.database.retrieve_activity_bests_for_user(user_id)

        # Cleanup the activity summary, removing any items that are no longer valid.
        old_activity_bests = {}
        if prune_activity_summary_cache:
            for old_activity_id in all_activity_bests:
                if self.activity_exists(old_activity_id):

                    # Activity still exists, add its data to the summary.
                    old_activity_bests = all_activity_bests[old_activity_id]
                    if Keys.ACTIVITY_TYPE_KEY in old_activity_bests and Keys.ACTIVITY_START_TIME_KEY in old_activity_bests:
                        old_activity_type = old_activity_bests[Keys.ACTIVITY_TYPE_KEY]
                        old_activity_time = old_activity_bests[Keys.ACTIVITY_START_TIME_KEY]
                        summarizer.add_activity_data(old_activity_id, old_activity_type, old_activity_time, old_activity_bests)
                else:

                    # Activity no longer exists, remove it's summary from the database.
                    self.database.delete_activity_best_for_user(user_id, old_activity_id)
        else:
            for old_activity_id in all_activity_bests:

                # Add this activity's data to the summary.
                old_activity_bests = all_activity_bests[old_activity_id]
                if len(old_activity_bests) > 0:
                    old_activity_type = old_activity_bests[Keys.ACTIVITY_TYPE_KEY]
                    old_activity_time = old_activity_bests[Keys.ACTIVITY_START_TIME_KEY]
                    summarizer.add_activity_data(old_activity_id, old_activity_type, old_activity_time, old_activity_bests)

        # Add data from the new activity.
        summarizer.add_activity_data(activity_id, activity_type, activity_time, activity_bests)

        # Create or update the personal records cache.
        if len(old_activity_bests) > 0:
            self.database.update_user_personal_records(user_id, summarizer.bests)
        else:
            self.database.create_user_personal_records(user_id, summarizer.bests)

        # Cache the summary data from this activity so we don't have to recompute everything again.
        return self.database.create_activity_bests(user_id, activity_id, activity_type, activity_time, activity_bests)

    def delete_all_user_personal_records(self, user_id):
        """Delete method for a user's personal record."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_all_user_personal_records(user_id)

    def retrieve_unanalyzed_activity_list(self, limit):
        if self.database is None:
            raise Exception("No database.")
        return self.database.retrieve_unanalyzed_activity_list(limit)

    def create_workout(self, user_id, workout_obj):
        """Create method for a workout."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if workout_obj is None:
            raise Exception("Bad parameter.")
        return self.database.create_workout(user_id, workout_obj)

    def retrieve_planned_workout(self, user_id, workout_id):
        """Retrieve method for the workout with the specified user and ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_planned_workout(user_id, workout_id)

    def retrieve_planned_workouts_for_user(self, user_id, start_time, end_time):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_planned_workouts_for_user(user_id, start_time, end_time)

    def retrieve_planned_workouts_calendar_id_for_user(self, user_id):
        """Retrieve method for the ical calendar ID for with specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_planned_workouts_calendar_id_for_user(user_id)

    def retrieve_planned_workouts_by_calendar_id(self, calendar_id):
        """Retrieve method for all workouts pertaining to the calendar with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if calendar_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_planned_workouts_by_calendar_id(calendar_id)

    def update_planned_workout(self, user_id, updated_workout_obj):
        """Create method for a workout."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if updated_workout_obj is None:
            raise Exception("Bad parameter.")
        
        workout_objs = self.database.retrieve_planned_workouts_for_user(user_id, None, None)
        new_workout_objs = [ workout_obj for workout_obj in workout_objs if workout_obj.workout_id != updated_workout_obj.workout_id ]
        new_workout_objs.append(updated_workout_obj)
        return self.database.update_planned_workouts_for_user(user_id, new_workout_objs)

    def delete_workouts_for_date_range(self, user_id, start_time, end_time):
        """Delete method for all workouts pertaining for the specified user within the given date range."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        new_workouts_list = []
        unix_start_time = int(time.mktime(start_time.timetuple()))
        unix_end_time = int(time.mktime(end_time.timetuple()))

        old_workouts_list = self.database.retrieve_planned_workouts_for_user(user_id, unix_start_time, unix_end_time)

        for workout in old_workouts_list:
            if workout.scheduled_time is not None and (workout.scheduled_time < start_time or workout.scheduled_time > end_time):
                new_workouts_list.append(workout)
        return self.database.update_planned_workouts_for_user(user_id, new_workouts_list)

    def retrieve_users_without_scheduled_workouts(self):
        """Returns a list of user IDs for users who have workout plans that need to be re-run."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.retrieve_users_without_scheduled_workouts()

    def retrieve_interval_workouts_for_user(self, user_id):
        """Retrieve method for all interval workouts associated with the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        pass

    def create_pace_plan(self, user_id, plan_name, plan_description, target_distance, target_distance_units, target_time, target_splits, target_splits_units, last_updated_time):
        """Create method for a pace plan."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if plan_name is None:
            raise Exception("Bad parameter.")
        if plan_description is None:
            raise Exception("Bad parameter.")
        if target_distance is None:
            raise Exception("Bad parameter.")
        if target_distance_units is None:
            raise Exception("Bad parameter.")
        if target_time is None:
            raise Exception("Bad parameter.")
        if target_splits is None:
            raise Exception("Bad parameter.")
        if target_splits_units is None:
            raise Exception("Bad parameter.")
        if last_updated_time is None:
            raise Exception("Bad parameter.")
        plan_id = uuid.uuid4()
        return self.database.create_pace_plan(user_id, plan_id, plan_name, plan_description, target_distance, target_distance_units, target_time, target_splits, target_splits_units, last_updated_time)

    def retrieve_pace_plans_for_user(self, user_id):
        """Retrieve method for all pace plans associated with the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_pace_plans(user_id)

    def update_pace_plan(self, user_id, plan_id, plan_name, plan_description, target_distance, target_distance_units, target_time, target_splits, target_splits_units, last_updated_time):
        """Update method for a pace plan."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if plan_id is None:
            raise Exception("Bad parameter.")
        if plan_name is None:
            raise Exception("Bad parameter.")
        if plan_description is None:
            raise Exception("Bad parameter.")
        if target_distance is None:
            raise Exception("Bad parameter.")
        if target_distance_units is None:
            raise Exception("Bad parameter.")
        if target_time is None:
            raise Exception("Bad parameter.")
        if target_splits is None:
            raise Exception("Bad parameter.")
        if target_splits_units is None:
            raise Exception("Bad parameter.")
        if last_updated_time is None:
            raise Exception("Bad parameter.")
        return self.database.update_pace_plan(user_id, plan_id, plan_name, plan_description, target_distance, target_distance_units, target_time, target_splits, target_splits_units, last_updated_time)

    def delete_pace_plan(self, user_id, plan_id):
        """Delete method for a user's pace plan."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if plan_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_pace_plan(user_id, plan_id)

    def create_gear(self, user_id, gear_type, gear_name, description, add_time, retire_time, last_updated_time):
        """Create method for gear."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_type is None:
            raise Exception("Bad parameter.")
        if gear_name is None:
            raise Exception("Bad parameter.")

        gear_id = uuid.uuid4()
        return self.database.create_gear(user_id, gear_id, gear_type, gear_name, description, add_time, retire_time, last_updated_time)

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

    def update_gear(self, user_id, gear_id, gear_type, gear_name, description, add_time, retire_time, updated_time):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        return self.database.update_gear(user_id, gear_id, gear_type, gear_name, description, add_time, retire_time, updated_time)

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

        # Retrieve the current gear defaults from the database.
        defaults = self.database.retrieve_gear_defaults(user_id)

        # Make sure all activity types are represented.
        all_activity_types = self.retrieve_activity_types()
        activities_with_defined_defaults = [item[Keys.ACTIVITY_TYPE_KEY] for item in defaults]
        for activity_type in all_activity_types:
            if activity_type not in activities_with_defined_defaults:
                defaults.append({Keys.ACTIVITY_TYPE_KEY: activity_type, Keys.GEAR_NAME_KEY: ""})
        return defaults

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
        if self.analysis_scheduler is None:
            raise Exception("No scheduler.")
        if user_id is None:
            raise Exception("Bad parameter.")
        self.analysis_scheduler.add_user_to_workout_plan_queue(user_id, self)

    def generate_workout_plan_from_inputs(self, user_id, inputs):
        """Generates a workout plan from the specified inputs."""
        if self.analysis_scheduler is None:
            raise Exception("No scheduler.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if inputs is None:
            raise Exception("Bad parameter.")
        self.analysis_scheduler.add_inputs_to_workout_plan_queue(user_id, inputs, self)

    def generate_api_key_for_user(self, user_id):
        """Generates a new API key for the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        key = str(uuid.uuid4()) # Create the API key
        rate = 100 # Only allow 100 requests per day
        return self.database.create_api_key(user_id, key, rate), key

    def delete_api_key(self, user_id, api_key):
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if api_key is None:
            raise Exception("Bad parameter.")
        return self.database.delete_api_key(user_id, api_key)

    def check_api_rate(self, api_key, max_rate):
        """Verifies that the API key is not being overused."""
        """Returns TRUE if it is fine to process the request, FALSE otherwise."""
        global g_api_key_rate_lock
        global g_api_key_rates
        global g_last_api_reset

        if self.database is None:
            raise Exception("No database.")
        if api_key is None:
            raise Exception("Bad parameter.")

        result = True
        g_api_key_rate_lock.acquire()

        # Once a day we should reset the countesr. This algorithm is overly simplistic and
        # could almost certainly be improved but is good enough for now.
        now = time.time()
        if now - g_last_api_reset > Units.SECS_PER_DAY:
            g_api_key_rates = {}
            g_last_api_reset = now

        # Check and increment the request count.
        try:
            current_rate = g_api_key_rates[api_key]
            result = current_rate <= max_rate
            g_api_key_rates[api_key] = current_rate + 1
        except:
            g_api_key_rates[api_key] = 1
        finally:
            g_api_key_rate_lock.release()
        return result

    def list_unsynched_activities(self, user_id, last_sync_date):
        """Returns a list of activity IDs with last modified times greater than the date provided."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if last_sync_date is None:
            raise Exception("Bad parameter.")

        return self.database.list_activities_with_last_updated_times_before(user_id, last_sync_date)

    def merge_activities(self, user_id, uploaded_file1_data, uploaded_file2_data):
        """Takes two recordings of the same activity and merges them into one."""
        if user_id is None:
            raise Exception("Bad parameter.")
        if uploaded_file1_data is None:
            raise Exception("Bad parameter.")
        if uploaded_file2_data is None:
            raise Exception("Bad parameter.")

        merge_tool = MergeTool.MergeTool()

    def create_race(self, user_id, race_name, race_date, race_distance, race_importance):
        """Adds a race to the user's calendar."""
        """Returns TRUE on success."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if race_name is None:
            raise Exception("Bad parameter.")
        if race_date is None:
            raise Exception("Bad parameter.")
        if race_distance is None:
            raise Exception("Bad parameter.")
        if race_importance is None:
            raise Exception("Bad parameter.")

        new_race = {}
        new_race[Keys.RACE_ID_KEY] = uuid.uuid4()
        new_race[Keys.RACE_NAME_KEY] = race_name
        new_race[Keys.RACE_DATE_KEY] = race_date
        new_race[Keys.RACE_DISTANCE_KEY] = race_distance
        new_race[Keys.RACE_IMPORTANCE_KEY] = race_importance

        user_races = self.database.retrieve_user_setting(user_id, Keys.USER_RACES)
        if user_races is None:
            user_races = []
        user_races.append(new_race)

        update_time = datetime.datetime.utcnow()
        return self.database.update_user_setting(user_id, Keys.USER_RACES, user_races, update_time)

    def delete_race(self, user_id, race_id):
        """Removes a race to the user's calendar."""
        """Returns TRUE on success."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if race_id is None:
            raise Exception("Bad parameter.")

        user_races = self.database.retrieve_user_setting(user_id, Keys.USER_RACES)
        updated_list = [x for x in user_races if str(x[Keys.RACE_ID_KEY]) != race_id]

        update_time = datetime.datetime.utcnow()
        return self.database.update_user_setting(user_id, Keys.USER_RACES, updated_list, update_time)

    def list_races(self, user_id):
        """Returns user's race calendar."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        user_races = self.database.retrieve_user_setting(user_id, Keys.USER_RACES)
        if user_races is None:
            user_races = []
        return user_races

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

        # Retrieve the summary data for each activity and update the heat map.
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

    def retrieve_bounded_activity_bests_for_user(self, user_id, cutoff_time_lower, cutoff_time_higher):
        """Return a dictionary of all best performances in the specified time frame."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if cutoff_time_lower is None:
            raise Exception("Bad parameter.")
        if cutoff_time_higher is None:
            raise Exception("Bad parameter.")

        summarizer = Summarizer.Summarizer()

        # Load cached summary data from all previous activities.
        all_activity_bests = self.database.retrieve_bounded_activity_bests_for_user(user_id, cutoff_time_lower, cutoff_time_higher)
        for activity_id in all_activity_bests:
            activity_bests = all_activity_bests[activity_id]
            summarizer.add_activity_data(activity_id, activity_bests[Keys.ACTIVITY_TYPE_KEY], activity_bests[Keys.ACTIVITY_START_TIME_KEY], activity_bests)

        # Output is a dictionary for each sport type.
        cycling_bests = summarizer.get_record_dictionary(Keys.TYPE_CYCLING_KEY)
        running_bests = summarizer.get_record_dictionary(Keys.TYPE_RUNNING_KEY)
        swimming_bests = summarizer.get_record_dictionary(Keys.TYPE_POOL_SWIMMING_KEY)
        cycling_summary = summarizer.get_summary_dictionary(Keys.TYPE_CYCLING_KEY)
        running_summary = summarizer.get_summary_dictionary(Keys.TYPE_RUNNING_KEY)
        swimming_summary = summarizer.get_summary_dictionary(Keys.TYPE_POOL_SWIMMING_KEY)
        return cycling_bests, running_bests, swimming_bests, cycling_summary, running_summary, swimming_summary

    def analyze_unanalyzed_activities(self, user_id, start_time, end_time):
        """Looks through the user's activities (within the given timeframe) and schedules any unanalyzed ones for analysis."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if start_time is None:
            raise Exception("Bad parameter.")
        if end_time is None:
            raise Exception("Bad parameter.")

        num_unanalyzed = 0

        all_activities = self.retrieve_user_activity_list(user_id, None, start_time, end_time, None)
        all_activity_bests = self.database.retrieve_bounded_activity_bests_for_user(user_id, start_time, end_time)

        for activity in all_activities:
            if Keys.ACTIVITY_START_TIME_KEY in activity and Keys.ACTIVITY_ID_KEY in activity:
                activity_id = activity[Keys.ACTIVITY_ID_KEY]
                activity_time = activity[Keys.ACTIVITY_START_TIME_KEY]
                if activity_time > start_time and activity_time <= end_time and activity_id not in all_activity_bests:
                    num_unanalyzed = num_unanalyzed + 1
                    self.analyze_activity_by_id(activity_id, user_id)

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
        all_activity_bests = self.database.retrieve_activity_bests_for_user(user_id)
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

    @staticmethod
    def update_training_intensity_cb(intensities, activity, user_id):
        if intensities is None:
            return
        if activity is not None and Keys.ACTIVITY_SUMMARY_KEY in activity:
            summary = activity[Keys.ACTIVITY_SUMMARY_KEY]
            if Keys.INTENSITY_SCORE in summary:
                activity_intensity = summary[Keys.INTENSITY_SCORE]
                intensities.append(activity_intensity)

    def compute_training_intensity_for_timeframe(self, user_id, start_time, end_time):
        """Returns the sum of intensity calculations for all activities logged between the start and end time."""
        num_unanalyzed_activities = self.analyze_unanalyzed_activities(user_id, start_time, end_time)
        if num_unanalyzed_activities > 0:
            raise Exception("Too many unanalyzed activities to sum activity intensities.")

        # Initialize.
        intensities = []

        if not self.retrieve_each_user_activity(user_id, intensities, DataMgr.update_training_intensity_cb, start_time, end_time, False):
            raise Exception("Error retrieving the user's activities.")

        return sum(intensities)

    def compute_run_training_paces(self, user_id, running_bests):
        """Computes the user's run training paces by searching the list of running 'bests' for the fastest 5K."""
        run_paces = {}
        if Keys.BEST_5K in running_bests:
            best_time_secs = running_bests[Keys.BEST_5K]
            calc = TrainingPaceCalculator.TrainingPaceCalculator()
            run_paces = calc.calc_from_race_distance_in_meters(5000, best_time_secs[0])
        return run_paces

    def compute_power_zone_distribution(self, ftp, powers):
        """Takes the list of power readings and determines how many belong in each power zone, based on the user's FTP."""
        calc = FtpCalculator.FtpCalculator()
        return calc.compute_power_zone_distribution(ftp, powers)

    def compute_heart_rate_zones(self, max_hr, resting_hr, age_in_years):
        """Returns an array containing the maximum heart rate for each training zone."""
        calc = HeartRateCalculator.HeartRateCalculator()
        return calc.training_zones(max_hr, resting_hr, age_in_years)

    def compute_power_training_zones(self, ftp):
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
        all_activity_types.extend(Keys.MULTISPORT_ACTIVITIES)
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
