# Copyright 2017 Michael J Simms
"""Data store abstraction"""

import StraenDb
import StraenKeys
import Importer

def get_activities_sort_key(item):
    # Was the start time provided? If not, look at the first location.
    if StraenKeys.ACTIVITY_TIME_KEY in item:
        return item[StraenKeys.ACTIVITY_TIME_KEY]
    return 0

class DataMgr(Importer.LocationWriter):
    """Data store abstraction"""

    def __init__(self, root_dir):
        self.database = StraenDb.MongoDatabase(root_dir)
        self.database.connect()
        super(Importer.LocationWriter, self).__init__()

    def terminate(self):
        """Destructor"""
        self.database = None

    def create_activity(self, username, stream_name, stream_description, activity_type):
        """Inherited from LocationWriter."""
        if self.database is None:
            raise Exception("No database.")
        return None, None

    def create_track(self, device_str, activity_id_str, track_name, track_description):
        """Inherited from LocationWriter."""
        pass

    def create_location(self, device_str, activity_id_str, date_time, latitude, longitude, altitude):
        """Inherited from LocationWriter. Create method for a location."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_location(device_str, activity_id_str, date_time, latitude, longitude, altitude)

    def create_locations(self, device_str, activity_id_str, locations):
        """Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_locations(device_str, activity_id_str, locations)

    def create_accelerometer_reading(self, device_str, activity_id_str, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_accelerometer_reading(device_str, activity_id_str, accels)

    def create_sensordata(self, activity_id_str, date_time, key, value):
        """Create method for sensor data."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_sensordata(activity_id_str, date_time, key, value)

    def create_metadata(self, activity_id_str, date_time, key, value, create_list):
        """Create method for activity metadata."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.create_metadata(activity_id_str, date_time, key, value, create_list)

    def import_file(self, username, local_file_name, file_extension):
        """Imports the contents of a local file into the database."""
        importer = Importer.Importer(self)
        return importer.import_file(username, local_file_name, file_extension)

    def update_activity_start_time(self, activity):
        """Caches the activity start time, based on the first reported location."""
        if StraenKeys.ACTIVITY_TIME_KEY in activity:
            return

        if StraenKeys.ACTIVITY_LOCATIONS_KEY in activity:
            locations = activity[StraenKeys.ACTIVITY_LOCATIONS_KEY]
        else:
            locations = self.retrieve_locations(activity[StraenKeys.ACTIVITY_ID_KEY])

        if len(locations) > 0:
            first_loc = locations[0]
            if StraenKeys.LOCATION_TIME_KEY in first_loc:
                time_num = first_loc[StraenKeys.LOCATION_TIME_KEY] / 1000 # Milliseconds to seconds
                activity_id_str = activity[StraenKeys.ACTIVITY_ID_KEY]
                activity[StraenKeys.ACTIVITY_TIME_KEY] = time_num
                self.create_metadata(activity_id_str, time_num, StraenKeys.ACTIVITY_TIME_KEY, time_num, False)

    def is_activity_public(self, activity):
        """Helper function for returning whether or not an activity is publically visible."""
        if StraenKeys.ACTIVITY_VISIBILITY_KEY in activity:
            if activity[StraenKeys.ACTIVITY_VISIBILITY_KEY] == "private":
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
                    device_activity[StraenKeys.REALNAME_KEY] = user_realname
                    self.update_activity_start_time(device_activity)
                activities.extend(device_activities)

        # List activities with no device that are associated with the user.

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
            more_activities = self.retrieve_user_activity_list(followed_user[StraenKeys.DATABASE_ID_KEY], followed_user[StraenKeys.REALNAME_KEY], start, num_results)
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

    def delete_activity(self, object_id):
        """Delete the activity with the specified object ID."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.delete_activity(object_id)

    def retrieve_activity_visibility(self, device_str, activity_id_str):
        """Returns the visibility setting for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_visibility(device_str, activity_id_str)

    def update_activity_visibility(self, activity_id_str, visibility):
        """Changes the visibility setting for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        if visibility is None:
            raise Exception("Bad parameter.")
        return self.database.update_activity_visibility(activity_id_str, visibility)

    def retrieve_locations(self, activity_id_str):
        """Returns the location list for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_locations(activity_id_str)

    def retrieve_accelerometer_readings(self, activity_id_str):
        """Returns the location list for the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_accelerometer_readings(activity_id_str)

    def retrieve_metadata(self, key, activity_id_str):
        """Returns all the sensordata for the specified sensor for the given activity."""
        if self.database is None:
            raise Exception("No database.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_metadata(key, activity_id_str)

    def retrieve_sensordata(self, key, activity_id_str):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if self.database is None:
            raise Exception("No database.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_sensordata(key, activity_id_str)

    def retrieve_most_recent_locations(self, activity_id_str, num):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_most_recent_locations(activity_id_str, num)

    def retrieve_most_recent_activity_id_for_device(self, device_str):
        """Returns the most recent activity id for the specified device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")
        activity = self.database.retrieve_most_recent_activity_for_device(device_str)
        if activity is None:
            return None
        return activity[StraenKeys.ACTIVITY_ID_KEY]

    def retrieve_most_recent_activity_for_device(self, device_str):
        """Returns the most recent activity for the specified device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_most_recent_activity_for_device(device_str)

    def create_tag(self, activity_id_str, tag):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        if tag is None or len(tag) == 0:
            raise Exception("Bad parameter.")
        return self.database.create_tag(activity_id_str, tag)

    def retrieve_tags(self, activity_id_str):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_tags(activity_id_str)

    def create_activity_comment(self, activity_id_str, commenter_id, comment):
        """Create method for a comment on an activity."""
        if self.database is None:
            raise Exception("No database.")
        if commenter_id is None:
            raise Exception("Bad parameter.")
        if comment is None or len(comment) == 0:
            raise Exception("Bad parameter.")
        return self.database.create_activity_comment(activity_id_str, commenter_id, comment)

    def retrieve_activity_comments(self, activity_id_str):
        """Returns a list containing all of the comments on the specified activity."""
        if self.database is None:
            raise Exception("No database.")
        if activity_id_str is None or len(activity_id_str) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_activity_comments(activity_id_str)

    def retrieve_activity_types(self):
        """Returns a the list of activity types that the software understands."""
        types = []
        types.append("Running")
        types.append("Cycling")
        types.append("Swimming")
        types.append("Push Ups / Press Ups")
        types.append("Pull Ups")
        return types
