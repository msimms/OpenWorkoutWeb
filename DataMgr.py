# Copyright 2017-2019 Michael J Simms
"""Data store abstraction"""

import time
import uuid
import FtpCalculator
import HeartRateCalculator
import Importer
import Keys
import MapSearch
import StraenDb
import Summarizer
import TrainingPaceCalculator

SIX_MONTHS = ((365.25 / 2.0) * 24.0 * 60.0 * 60.0)
ONE_YEAR = (365.25 * 24.0 * 60.0 * 60.0)
FOUR_WEEKS = (14.0 * 24.0 * 60.0 * 60.0)

def get_activities_sort_key(item):
    # Was the start time provided? If not, look at the first location.
    if Keys.ACTIVITY_TIME_KEY in item:
        return item[Keys.ACTIVITY_TIME_KEY]
    return 0

class DataMgr(Importer.ActivityWriter):
    """Data store abstraction"""

    def __init__(self, root_url, root_dir, analysis_scheduler, import_scheduler, workout_plan_gen_scheduler):
        self.database = StraenDb.MongoDatabase(root_dir)
        self.database.connect()
        self.root_url = root_url
        self.analysis_scheduler = analysis_scheduler
        self.import_scheduler = import_scheduler
        self.workout_plan_gen_scheduler = workout_plan_gen_scheduler
        self.map_search = None
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

    def analyze(self, activity, activity_user_id):
        """Schedules the specified activity for analysis."""
        self.analysis_scheduler.add_to_queue(activity, activity_user_id)

    def compute_end_time(self, activity):
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

    def compute_and_store_end_time(self, activity):
        """Examines the activity and computes the time at which the activity ended, storing it so we don't have to do this again."""
        if self.database is None:
            raise Exception("No database.")

        end_time = self.compute_end_time(activity)

        # If we couldn't find anything with a time then just duplicate the start time, assuming it's a manually entered workout or something.
        if end_time is None:
            end_time = activity[Keys.ACTIVITY_TIME_KEY]

        # Store the end time, so we don't have to go through this again.
        if end_time is not None:
            activity_id = activity[Keys.ACTIVITY_ID_KEY]
            self.database.create_metadata(activity_id, end_time, Keys.ACTIVITY_END_TIME_KEY, end_time / 1000, False)

        return end_time

    def is_duplicate_activity(self, user_id, start_time):
        """Inherited from ActivityWriter. Returns TRUE if the activity appears to be a duplicate of another activity. Returns FALSE otherwise."""
        if self.database is None:
            raise Exception("No database.")

        activities = self.database.retrieve_user_activity_list(user_id, None, None, None)
        for activity in activities:
            if Keys.ACTIVITY_TIME_KEY in activity:

                # We're looking for activities that start within the bounds of another activity.
                activity_start_time = activity[Keys.ACTIVITY_TIME_KEY]
                if start_time == activity_start_time:
                    return True
                if start_time > activity_start_time:
                    if Keys.ACTIVITY_END_TIME_KEY not in activity:
                        activity_end_time = self.compute_and_store_end_time(activity)
                    else:
                        activity_end_time = activity[Keys.ACTIVITY_END_TIME_KEY]

                    if activity_end_time and start_time < activity_end_time:
                        return True

        return False

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time):
        """Inherited from ActivityWriter. Called when we start reading an activity file."""
        if self.database is None:
            raise Exception("No database.")

        device_str = ""
        activity_id = self.create_activity_id()

        if not self.database.create_activity(activity_id, stream_name, start_time, device_str):
            return None, None
        if activity_type is not None and len(activity_type) > 0:
            self.database.create_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, activity_type, False)
        if user_id is not None:
            self.database.create_metadata(activity_id, 0, Keys.ACTIVITY_USER_ID_KEY, user_id, False)
        return device_str, activity_id

    def create_track(self, device_str, activity_id, track_name, track_description):
        """Inherited from ActivityWriter."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Inherited from ActivityWriter. Create method for a location."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_location(device_str, activity_id, date_time, latitude, longitude, altitude)

    def create_locations(self, device_str, activity_id, locations):
        """Inherited from ActivityWriter. Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_locations(device_str, activity_id, locations)

    def create_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Inherited from ActivityWriter. Create method for sensor data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_sensor_reading(activity_id, date_time, sensor_type, value)

    def create_sensor_readings(self, activity_id, sensor_type, values):
        """Inherited from ActivityWriter. Adds several sensor readings to the database. 'values' is an array of arrays in the form [time, value]."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_sensor_readings(activity_id, sensor_type, values)

    def create_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_metadata(activity_id, date_time, key, value, create_list)

    def create_metadata_list(self, activity_id, key, values):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_metadata_list(activity_id, key, values)

    def create_sets_and_reps_data(self, activity_id, sets):
        """Create method for activity set and rep data."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_sets_and_reps_data(activity_id, sets)

    def create_accelerometer_reading(self, device_str, activity_id, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_accelerometer_reading(device_str, activity_id, accels)

    def finish_activity(self, activity_id, end_time):
        """Inherited from ActivityWriter. Called for post-processing."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None:
            raise Exception("No activity ID.")
        return self.database.create_metadata(activity_id, end_time, Keys.ACTIVITY_END_TIME_KEY, end_time / 1000, False)

    def import_file(self, username, user_id, local_file_name, uploaded_file_name):
        """Imports the contents of a local file into the database."""
        if self.import_scheduler is None:
            raise Exception("No importer.")
        if username is None:
            raise Exception("No username.")
        if user_id is None:
            raise Exception("No user ID.")
        if local_file_name is None:
            raise Exception("No local file name.")
        if uploaded_file_name is None:
            raise Exception("No uploaded file name.")
        self.import_scheduler.add_to_queue(username, user_id, local_file_name, uploaded_file_name)

    def update_activity_start_time(self, activity):
        """Caches the activity start time, based on the first reported location."""
        if Keys.ACTIVITY_TIME_KEY in activity:
            return

        if Keys.ACTIVITY_LOCATIONS_KEY in activity:
            locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
        else:
            locations = self.retrieve_locations(activity[Keys.ACTIVITY_ID_KEY])

        if len(locations) > 0:
            first_loc = locations[0]
            if Keys.LOCATION_TIME_KEY in first_loc:
                time_num = first_loc[Keys.LOCATION_TIME_KEY] / 1000 # Milliseconds to seconds
                activity_id = activity[Keys.ACTIVITY_ID_KEY]
                activity[Keys.ACTIVITY_TIME_KEY] = time_num
                self.create_metadata(activity_id, time_num, Keys.ACTIVITY_TIME_KEY, time_num, False)

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
                for device_activity in device_activities:
                    device_activity[Keys.REALNAME_KEY] = user_realname
                    self.update_activity_start_time(device_activity)
                activities.extend(device_activities)

        # List activities with no device that are associated with the user.
        exclude_keys = self.database.list_excluded_keys() # Things we don't need.
        user_activities = self.database.retrieve_user_activity_list(user_id, start, None, exclude_keys)
        for user_activity in user_activities:
            user_activity[Keys.REALNAME_KEY] = user_realname
        activities.extend(user_activities)

        # Sort and limit the list.
        if len(activities) > 0:
            activities = sorted(activities, key=get_activities_sort_key, reverse=True)[:num_results]
        return activities

    def retrieve_all_activities_visible_to_user(self, user_id, user_realname, start, num_results):
        """Returns a list containing all of the activities visible to the specified user, up to num_results. num_results can be None for all activiites."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")

        # Start with the user's own activities.
        activities = self.retrieve_user_activity_list(user_id, user_realname, start, num_results)

        # Add the activities of users they follow.
        followed_users = self.database.retrieve_users_followed(user_id)
        for followed_user in followed_users:
            more_activities = self.retrieve_user_activity_list(followed_user[Keys.DATABASE_ID_KEY], followed_user[Keys.REALNAME_KEY], start, num_results)
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

    def delete_activity(self, object_id):
        """Delete the activity with the specified object ID."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.delete_activity(object_id)

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

    def retrieve_locations(self, activity_id):
        """Returns the location list for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_locations(activity_id)

    def retrieve_most_recent_locations(self, activity_id, num):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_most_recent_locations(activity_id, num)

    def retrieve_sensor_readings(self, key, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if self.database is None:
            raise Exception("No database.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_sensor_readings(key, activity_id)

    def retrieve_metadata(self, key, activity_id):
        """Returns all the sensordata for the specified sensor for the given activity."""
        if self.database is None:
            raise Exception("No database.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_metadata(key, activity_id)

    def retrieve_accelerometer_readings(self, activity_id):
        """Returns the location list for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id is None or len(activity_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_accelerometer_readings(activity_id)

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
                elif Keys.ACTIVITY_TIME_KEY in device_activity and Keys.ACTIVITY_TIME_KEY in most_recent_activity:
                    curr_activity_time = device_activity[Keys.ACTIVITY_TIME_KEY]
                    prev_activity_time = most_recent_activity[Keys.ACTIVITY_TIME_KEY]
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
        tags.append('Hot')
        tags.append('Humid')
        tags.append('Cold')
        tags.append('Rainy')
        tags.append('Windy')
        tags.append('Virtual')
        return tags

    def list_tags_for_activity_type_and_user(self, user_id, activity_type):
        """Returns a list of tags that are valid for a particular activity type."""
        tags = self.list_default_tags()
        gear_list = self.retrieve_gear_for_user(user_id)
        show_shoes = activity_type in Keys.FOOT_BASED_ACTIVITIES
        show_bikes = activity_type in Keys.BIKE_BASED_ACTIVITIES
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

    def associate_tag_with_activity(self, activity, tag):
        """Adds a tag to an activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity is None:
            raise Exception("Bad parameter.")
        if tag is None:
            raise Exception("Bad parameter.")
        return self.database.create_tag_on_activity(activity, tag)

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
        distance = DataMgr.distance_for_activity(activity)
        for key in tag_distances.keys():
            tag_distances[key] = tag_distances[key] + distance

    def distance_for_tags(self, user_id, tags):
        """Computes the distance (in meters) for activities with the combination of user and tag."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if tags is None:
            raise Exception("Bad parameter.")

        tag_distances = {}
        for tag in tags:
            tag_distances[tag] = 0.0
        self.database.retrieve_each_user_activity(tag_distances, user_id, DataMgr.distance_for_tag_cb)
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

    def insert_bests_from_activity(self, user_id, activity_id, activity_type, activity_time, bests):
        """Update method for a user's personal record."""
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

        # This object will keep track of the PRs.
        summarizer = Summarizer.Summarizer()

        # Load existing PRs.
        all_personal_records = self.database.retrieve_user_personal_records(user_id)
        for record_activity_type in all_personal_records.keys():
            summarizer.set_record_dictionary(record_activity_type, all_personal_records[record_activity_type])
        do_update = len(all_personal_records) > 0

        # Add data from the new activity.
        summarizer.add_activity_data(activity_id, activity_type, activity_time, bests)
 
        # Create or update the PR list.
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

    def retrieve_workouts_for_user(self, user_id):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_workouts_for_user(user_id)

    def delete_workout(self, workout_id):
        if self.database is None:
            raise Exception("No database.")
        if workout_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_workout(workout_id)

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

    def retrieve_gear_for_user(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_gear_for_user(user_id)

    def retrieve_gear_of_specified_type_for_user(self, user_id, gear_type):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_type is None:
            raise Exception("Bad parameter.")

        final_gear_list = []
        gear_list = self.database.retrieve_gear_for_user(user_id)
        for gear in gear_list:
            if Keys.GEAR_TYPE_KEY in gear:
                if gear_type == gear[Keys.GEAR_TYPE_KEY]:
                    final_gear_list.append(gear)
        return final_gear_list

    def update_gear(self, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        if gear_type is None:
            raise Exception("Bad parameter.")
        if gear_name is None:
            raise Exception("Bad parameter.")
        if gear_description is None:
            raise Exception("Bad parameter.")
        return self.database.update_gear(gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time)

    def delete_gear(self, user_id, gear_id):
        """Delete method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if gear_id is None:
            raise Exception("Bad parameter.")
        return self.database.delete_gear(user_id, gear_id)

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

    def retrieve_each_user_activity(self, context, user_id, cb=None):
        """Makes sure that summary data exists for all of the user's activities."""
        if self.database is None:
            raise Exception("No database.")
        if context is None:
            raise Exception("Bad parameter.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if cb is None:
            raise Exception("Bad parameter.")
        self.database.retrieve_each_user_activity(context, user_id, cb)

    def associate_gear_with_activity(self, activity, gear_name):
        """Adds gear to an activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity is None:
            raise Exception("Bad parameter.")
        if gear_name is None:
            raise Exception("Bad parameter.")
        return self.database.create_gear_on_activity(activity, gear_name)

    def generate_workout_plan(self, user_id):
        """Generates/updates a workout plan for the user with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        self.workout_plan_gen_scheduler.add_to_queue(user_id)

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
        locations = self.retrieve_locations(activity_id)
        if locations and len(locations) > 0:
            first_loc = locations[0]
            location_description = self.map_search.search_map(float(first_loc[Keys.LOCATION_LAT_KEY]), float(first_loc[Keys.LOCATION_LON_KEY]))
        return location_description

    def compute_recent_bests(self, user_id, timeframe):
        """Return a dictionary of all best performances in the specified time frame."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if timeframe is None:
            raise Exception("Bad parameter.")

        summarizer = Summarizer.Summarizer()

        # Load cached summary data from all previous activities.
        if timeframe > 0:
            cutoff_time = time.time() - timeframe
        else:
            cutoff_time = 0
        all_activity_bests = self.database.retrieve_recent_activity_bests_for_user(user_id, cutoff_time)
        if all_activity_bests is not None:
            for activity_id in all_activity_bests:
                activity_bests = all_activity_bests[activity_id]
                if Keys.ACTIVITY_TYPE_KEY in activity_bests and Keys.ACTIVITY_TIME_KEY in activity_bests:
                    summarizer.add_activity_data(activity_id, activity_bests[Keys.ACTIVITY_TYPE_KEY], activity_bests[Keys.ACTIVITY_TIME_KEY], activity_bests)

        cycling_bests = summarizer.get_record_dictionary(Keys.TYPE_CYCLING_KEY)
        running_bests = summarizer.get_record_dictionary(Keys.TYPE_RUNNING_KEY)
        return cycling_bests, running_bests

    def compute_bests(self, user_id, activity_type, key):
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
        summarizer = Summarizer.Summarizer()

        # Load cached summary data from all previous activities.
        all_activity_bests = self.database.retrieve_recent_activity_bests_for_user(user_id, 0)
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

    def compute_run_training_paces(self, user_id, running_bests):
        run_paces = []
        calc = TrainingPaceCalculator.TrainingPaceCalculator()
        if Keys.BEST_5K in running_bests:
            best_time = running_bests[Keys.BEST_5K]
            best_time_secs = best_time[0] / 60
            run_paces = calc.calc_from_race_distance_in_meters(5000, best_time_secs)
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
        types = []
        types.append(Keys.TYPE_RUNNING_KEY)
        types.append(Keys.TYPE_HIKING_KEY)
        types.append(Keys.TYPE_CYCLING_KEY)
        types.append(Keys.TYPE_SWIMMING_KEY)
        types.append(Keys.TYPE_PULL_UPS_KEY)
        types.append(Keys.TYPE_PUSH_UPS_KEY)
        return types
