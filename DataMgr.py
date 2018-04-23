# Copyright 2017 Michael J Simms
"""Data store abstraction"""

import StraenDb
import Importer


class DataMgr(Importer.LocationWriter):
    """Data store abstraction"""

    def __init__(self, root_dir):
        self.database = StraenDb.MongoDatabase(root_dir)
        self.database.connect()
        super(Importer.LocationWriter, self).__init__()

    def terminate(self):
        """Destructor"""
        self.database = None

    def create(self, username, stream_name, stream_description, activity_type):
        """Inherited from LocationWriter."""
        return None, None

    def create_track(self, device_str, activity_id, track_name, track_description):
        """Inherited from LocationWriter."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Inherited from LocationWriter. Create method for a location."""
        if self.database is None:
            return None, "No database."

        return self.database.create_location(device_str, activity_id, date_time, latitude, longitude, altitude)

    def import_file(self, username, local_file_name, file_extension):
        """Imports the contents of a local file into the database."""
        importer = Importer.Importer(self)
        return importer.import_file(username, local_file_name, file_extension)

    def retrieve_user_activities(self, user_id, start, num_results):
        """Returns a list containing all of the user's activities, up to num_results."""
        if self.database is None:
            return None, "No database."
        if user_id is None or len(user_id) == 0:
            return None, "Bad parameter."

        activities = []
        devices = self.database.retrieve_user_devices(user_id)
        if devices is not None:
            for device in devices:
                device_activities = self.database.retrieve_device_activities(device, start, num_results)
                activities.extend(device_activities)
        return activities

    def retrieve_activity_visibility(self, device_str, activity_id):
        """Returns the visibility setting for the specified activity."""
        if self.database is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.database.retrieve_activity_visibility(device_str, activity_id)

    def update_activity_visibility(self, device_str, activity_id, visibility):
        """Changes the visibility setting for the specified activity."""
        if self.database is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        if visibility is None:
            return None, "Bad parameter."
        return self.database.update_activity_visibility(device_str, activity_id, visibility)

    def retrieve_locations(self, device_str, activity_id):
        """Returns the location list for the specified activity."""
        if self.database is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.database.retrieve_locations(device_str, activity_id)

    def retrieve_metadata(self, key, device_str, activity_id):
        """Returns all the sensordata for the specified sensor for the given activity."""
        if self.database is None:
            return None, "No database."
        if key is None or len(key) == 0:
            return None, "Bad parameter."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.database.retrieve_metadata(key, device_str, activity_id)

    def retrieve_sensordata(self, key, device_str, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if self.database is None:
            return None, "No database."
        if key is None or len(key) == 0:
            return None, "Bad parameter."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.database.retrieve_sensordata(key, device_str, activity_id)

    def retrieve_most_recent_locations(self, device_str, activity_id, num):
        """Returns the most recent 'num' locations for the specified device and activity."""
        if self.database is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        if activity_id is None:
            return None, "Bad parameter."
        return self.database.retrieve_most_recent_locations(device_str, activity_id, num)

    def retrieve_most_recent_activity_id_for_device(self, device_str):
        """Returns the most recent activity id for the specified device."""
        if self.database is None:
            return None, "No database."
        if device_str is None or len(device_str) == 0:
            return None, "Bad parameter."
        return self.database.retrieve_most_recent_activity_id_for_device(device_str)
