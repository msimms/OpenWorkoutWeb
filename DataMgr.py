# Copyright 2017 Michael J Simms
"""Data store abstraction"""

import uuid
import FtpCalculator
import HeartRateCalculator
import Importer
import Keys
import StraenDb
import Summarizer

def get_activities_sort_key(item):
    # Was the start time provided? If not, look at the first location.
    if Keys.ACTIVITY_TIME_KEY in item:
        return item[Keys.ACTIVITY_TIME_KEY]
    return 0

class DataMgr(Importer.ActivityWriter):
    """Data store abstraction"""

    def __init__(self, root_dir, analysis_scheduler, import_scheduler):
        self.database = StraenDb.MongoDatabase(root_dir)
        self.database.connect()
        self.analysis_scheduler = analysis_scheduler
        self.import_scheduler = import_scheduler
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

    def is_duplicate_activity(self, user_id, start_time):
        """Inherited from ActivityWriter. Returns TRUE if the activity appears to be a duplicate of another activity. Returns FALSE otherwise."""
        if self.database is None:
            raise Exception("No database.")

        exclude_keys = self.database.list_excluded_keys() # Things we don't need.
        activities = self.database.retrieve_user_activity_list(user_id, None, None, exclude_keys)
        for activity in activities:
            if Keys.ACTIVITY_TIME_KEY in activity:
                activity_start_time = activity[Keys.ACTIVITY_TIME_KEY]
                if start_time > activity_start_time: # Need to incorporate check agains the activity end time, but in an efficient manner.
                    pass
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
        return self.database.create_locations(device_str, activity_id, locations)

    def create_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Inherited from ActivityWriter. Create method for sensor data."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_sensor_reading(activity_id, date_time, sensor_type, value)

    def create_sensor_readings(self, activity_id, sensor_type, values):
        """Inherited from ActivityWriter. Adds several sensor readings to the database. 'values' is an array of arrays in the form [time, value]."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_sensor_readings(activity_id, sensor_type, values)

    def create_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_metadata(activity_id, date_time, key, value, create_list)

    def create_metadata_list(self, activity_id, key, values):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_metadata_list(activity_id, key, values)

    def create_sets_and_reps_data(self, activity_id, sets):
        """Create method for activity set and rep data."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_sets_and_reps_data(activity_id, sets)

    def create_accelerometer_reading(self, device_str, activity_id, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_accelerometer_reading(device_str, activity_id, accels)

    def finish_activity(self):
        """Inherited from ActivityWriter. Called for post-processing."""
        pass

    def import_file(self, username, user_id, local_file_name, uploaded_file_name):
        """Imports the contents of a local file into the database."""
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
        tags.append('Virtual')
        tags.append('Hot')
        tags.append('Humid')
        tags.append('Cold')
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

    def create_activity_comment(self, activity_id, commenter_id, comment):
        """Create method for a comment on an activity."""
        if self.database is None:
            raise Exception("No database.")
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
        return self.database.store_user_setting(user_id, Keys.ESTIMATED_FTP_KEY, estimated_ftp)

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

        # This object will keep track of the PRs.
        summarizer = Summarizer.Summarizer()

        # Load existing PRs.
        all_personal_records = self.database.retrieve_user_personal_records(user_id)
        for record_activity_type in all_personal_records.keys():
            summarizer.set_record_dictionary(record_activity_type, all_personal_records[record_activity_type])
        do_update = len(all_personal_records) > 0

        # Load cached summary data from all previous activities.
        cached_activity_bests = self.database.retrieve_activity_bests(user_id)
        for cached_activity_data in cached_activity_bests:
            pass

        # Add data from the new activity.
        summarizer.add_activity_data(activity_id, activity_type, activity_time, bests)
 
        # Create or update the PR list.
        all_personal_records[activity_type] = summarizer.get_record_dictionary(activity_type)
        if do_update:
            self.database.update_user_personal_records(user_id, all_personal_records)
        else:
            self.database.create_user_personal_records(user_id, all_personal_records)

        # Cache the summary data from this activity so we don't have to recompute everything again.
        return self.database.create_activity_bests(user_id, activity_id, activity_time, bests)

    def retrieve_user_personal_records(self, user_id):
        """Retrieve method for a user's personal record."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user_personal_records(user_id)

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
        return self.database.create_gear(user_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time)

    def retrieve_gear_for_user(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_gear_for_user(user_id)

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

    @staticmethod
    def update_summary_data_cb(context, activity, user_id):
        """Callback function for update_summary_data."""
        if Keys.ACTIVITY_SUMMARY_KEY not in activity:
            context.analyze(activity, user_id)

    def update_summary_data(self, user_id):
        """Makes sure that summary data exists for all of the user's activities."""
        if self.database is None:
            raise Exception("No database.")
        self.database.retrieve_each_user_activity(self, user_id, DataMgr.update_summary_data_cb)

    def generate_workout_plan(self, user_id):
        """Generates/updates a workout plan for the user with the specified ID."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        self.update_summary_data(user_id)

    def retrieve_activity_types(self):
        """Returns a the list of activity types that the software understands."""
        types = []
        types.append("Running")
        types.append("Cycling")
        types.append("Swimming")
        types.append("Push Ups / Press Ups")
        types.append("Pull Ups")
        return types

    def retrieve_heart_rate_zones(self, max_hr):
        """Returns an array containing the maximum heart rate for each training zone."""
        calc = HeartRateCalculator.HeartRateCalculator()
        return calc.training_zones(max_hr)

    def retrieve_power_training_zones(self, ftp):
        """Returns an array containing the maximum power rate for each training zone."""
        calc = FtpCalculator.FtpCalculator()
        return calc.power_training_zones(ftp)
