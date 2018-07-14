# Copyright 2017 Michael J Simms
"""Database implementation"""

import sys
import traceback
from bson.objectid import ObjectId
import pymongo
import Database
import StraenKeys


def retrieve_time_from_location(location):
    """Used with the sort function."""
    return location['time']

def retrieve_time_from_time_value_pair(value):
    """Used with the sort function."""
    return value.keys()[0]


class Device(object):
    def __init__(self):
        self.id = 0
        self.name = ""
        self.description = ""
        super(Device, self).__init__()


class MongoDatabase(Database.Database):
    """Mongo DB implementation of the Straen database."""
    conn = None
    database = None
    users_collection = None
    activities_collection = None

    def __init__(self, rootDir):
        Database.Database.__init__(self, rootDir)

    def connect(self):
        """Connects/creates the database"""
        try:
            self.conn = pymongo.MongoClient('localhost:27017')
            self.database = self.conn['straendb']
            self.users_collection = self.database['users']
            self.activities_collection = self.database['activities']
            return True
        except pymongo.errors.ConnectionFailure, e:
            self.log_error("Could not connect to MongoDB: %s" % e)
        return False

    def create_user(self, username, realname, passhash):
        """Create method for a user."""
        if username is None:
            self.log_error(MongoDatabase.create_user.__name__ + ": Unexpected empty object: username")
            return False
        if realname is None:
            self.log_error(MongoDatabase.create_user.__name__ + ": Unexpected empty object: realname")
            return False
        if passhash is None:
            self.log_error(MongoDatabase.create_user.__name__ + ": Unexpected empty object: passhash")
            return False
        if len(username) == 0:
            self.log_error(MongoDatabase.create_user.__name__ + ": username too short")
            return False
        if len(realname) == 0:
            self.log_error(MongoDatabase.create_user.__name__ + ": realname too short")
            return False
        if len(passhash) == 0:
            self.log_error(MongoDatabase.create_user.__name__ + ": hash too short")
            return False

        try:
            post = {StraenKeys.USERNAME_KEY: username, StraenKeys.REALNAME_KEY: realname, StraenKeys.HASH_KEY: passhash, StraenKeys.DEVICES_KEY: [], StraenKeys.FOLLOWING_KEY: [], StraenKeys.DEFAULT_PRIVACY: StraenKeys.ACTIVITY_VISIBILITY_PUBLIC}
            self.users_collection.insert(post)
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user(self, username):
        """Retrieve method for a user."""
        if username is None:
            self.log_error(MongoDatabase.retrieve_user.__name__ + ": Unexpected empty object: username")
            return None, None, None
        if len(username) == 0:
            self.log_error(MongoDatabase.retrieve_user.__name__ + ": username is empty")
            return None, None, None

        try:
            user = self.users_collection.find_one({StraenKeys.USERNAME_KEY: username})
            if user is not None:
                return str(user[StraenKeys.DATABASE_ID_KEY]), user[StraenKeys.HASH_KEY], user[StraenKeys.REALNAME_KEY]
            return None, None, None
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None, None, None

    def retrieve_user_from_id(self, user_id):
        """Retrieve method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_from_id.__name__ + ": Unexpected empty object: user_id")
            return None, None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                return user[StraenKeys.USERNAME_KEY], user[StraenKeys.REALNAME_KEY]
            return None, None
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None, None

    def update_user(self, user_id, username, realname, passhash):
        """Update method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.update_user.__name__ + ": Unexpected empty object: user_id")
            return None
        if username is None:
            self.log_error(MongoDatabase.update_user.__name__ + ": Unexpected empty object: username")
            return False
        if realname is None:
            self.log_error(MongoDatabase.update_user.__name__ + ": Unexpected empty object: realname")
            return False
        if len(username) == 0:
            self.log_error(MongoDatabase.update_user.__name__ + ": username too short")
            return False
        if len(realname) == 0:
            self.log_error(MongoDatabase.update_user.__name__ + ": realname too short")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                user[StraenKeys.USERNAME_KEY] = username
                user[StraenKeys.REALNAME_KEY] = realname
                if passhash is not None:
                    user[StraenKeys.HASH_KEY] = passhash
                self.users_collection.save(user)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def delete_user(self, user_id):
        """Delete method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_user.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.delete_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_matched_users(self, username):
        """Returns a list of user names for users that match the specified regex."""
        user_list = []

        if username is None:
            self.log_error(MongoDatabase.retrieve_matched_users.__name__ + ": Unexpected empty object: username")
            return user_list
        if len(username) == 0:
            self.log_error(MongoDatabase.retrieve_matched_users.__name__ + ": username is empty")
            return user_list

        try:
            matched_users = self.users_collection.find({StraenKeys.USERNAME_KEY: {"$regex": username}})
            if matched_users is not None:
                for matched_user in matched_users:
                    user_list.append(matched_user[StraenKeys.USERNAME_KEY])
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return user_list

    def create_user_device(self, user_id, device_str):
        """Create method for a device."""
        if user_id is None:
            self.log_error(MongoDatabase.create_user_device.__name__ + ": Unexpected empty object: user_id")
            return False
        if device_str is None:
            self.log_error(MongoDatabase.create_user_device.__name__ + ": Unexpected empty object: device_str")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            devices = []
            if user is not None:
                if StraenKeys.DEVICES_KEY in user:
                    devices = user[StraenKeys.DEVICES_KEY]
            if device_str not in devices:
                devices.append(device_str)
                user[StraenKeys.DEVICES_KEY] = devices
                self.users_collection.save(user)
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return True

    def retrieve_user_devices(self, user_id):
        """Retrieve method for a device."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_devices.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                if StraenKeys.DEVICES_KEY in user:
                    return user[StraenKeys.DEVICES_KEY]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user_from_device(self, device_str):
        """Finds the user associated with the device."""
        if self.database is None:
            raise Exception("No database.")
        if len(device_str) == 0:
            return False, "Device string not provided."

        try:
            return self.users_collection.find_one({"devices": device_str})
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def delete_user_device(self, device_str):
        """Deletes method for a device."""
        if device_str is None:
            self.log_error(MongoDatabase.delete_user_device.__name__ + ": Unexpected empty object: device_str")
            return False

        try:
            self.activities_collection.remove({StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str})
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_users_followed(self, user_id):
        """Returns the user ids for all users that are followed by the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_users_followed.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                if StraenKeys.FOLLOWING_KEY in user:
                    following_ids = user[StraenKeys.FOLLOWING_KEY]
                    following_users = []
                    for following_id in following_ids:
                        username, realname = self.retrieve_user_from_id(following_id)
                        user = {}
                        user[StraenKeys.DATABASE_ID_KEY] = following_id
                        user[StraenKeys.USERNAME_KEY] = username
                        user[StraenKeys.REALNAME_KEY] = realname
                        following_users.append(user)
                    return following_users
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_followers(self, user_id):
        """Returns the user ids for all users that follow the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_followers.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            followers = self.users_collection.find({StraenKeys.FOLLOWING_KEY: user_id})
            return list(followers)
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_following_entry(self, user_id, target_id):
        """Appends a user to the followers list of the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.create_following_entry.__name__ + ": Unexpected empty object: user_id")
            return None
        if target_id is None:
            self.log_error(MongoDatabase.create_following_entry.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                user_list = []
                if StraenKeys.FOLLOWING_KEY in user:
                    user_list = user[StraenKeys.FOLLOWING_KEY]
                if target_id not in user_list:
                    user_list.append(target_id)
                    user[StraenKeys.FOLLOWING_KEY] = user_list
                    self.users_collection.save(user)
                    return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def update_user_setting(self, user_id, key, value):
        """Create/update method for user preferences."""
        if user_id is None:
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: user_id")
            return False
        if key is None:
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: key")
            return False
        if value is None:
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: value")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                user[key] = value
                self.users_collection.save(user)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user_setting(self, user_id, key):
        """Retrieve method for user preferences."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_setting.__name__ + ": Unexpected empty object: user_id")
            return None
        if key is None:
            self.log_error(MongoDatabase.retrieve_user_setting.__name__ + ": Unexpected empty object: key")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({StraenKeys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                if key in user:
                    return user[key]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_device_activity_list(self, device_str, start, num_results):
        """Retrieves the list of activities associated with the specified device."""
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_device_activity_list.__name__ + ": Unexpected empty object: device_str")
            return None
        if num_results is not None and num_results <= 0:
            return None

        try:
            # Things we don't need.
            exclude_keys = {}
            exclude_keys[StraenKeys.APP_CADENCE_KEY] = False
            exclude_keys[StraenKeys.APP_CURRENT_SPEED_KEY] = False
            exclude_keys[StraenKeys.APP_AVG_SPEED_KEY] = False
            exclude_keys[StraenKeys.APP_MOVING_SPEED_KEY] = False
            exclude_keys[StraenKeys.APP_HEART_RATE_KEY] = False
            exclude_keys[StraenKeys.APP_AVG_HEART_RATE_KEY] = False
            exclude_keys[StraenKeys.APP_CURRENT_PACE_KEY] = False
            exclude_keys[StraenKeys.APP_POWER_KEY] = False
            exclude_keys[StraenKeys.ACTIVITY_LOCATIONS_KEY] = False

            if start is None and num_results is None:
                return list(self.activities_collection.find({StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(StraenKeys.DATABASE_ID_KEY, -1))
            elif num_results is None:
                return list(self.activities_collection.find({StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(StraenKeys.DATABASE_ID_KEY, -1).skip(start))
            else:
                return list(self.activities_collection.find({StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(StraenKeys.DATABASE_ID_KEY, -1).skip(start).limit(num_results))
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_most_recent_activity_for_device(self, device_str):
        """Retrieves the ID for the most recent activity to be associated with the specified device."""
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_most_recent_activity_for_device.__name__ + ": Unexpected empty object: device_str")
            return None

        try:
            device_activities = self.activities_collection.find({StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str}).sort(StraenKeys.DATABASE_ID_KEY, -1).limit(1)
            if device_activities is not None and device_activities.count() > 0:
                activity = device_activities.next()
                return activity
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity(self, activity_id_str, activty_name, date_time, device_str):
        """Create method for an activity."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.create_activity.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if activty_name is None:
            self.log_error(MongoDatabase.create_activity.__name__ + ": Unexpected empty object: activty_name")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_activity.__name__ + ": Unexpected empty object: date_time")
            return False
        if device_str is None:
            self.log_error(MongoDatabase.create_activity.__name__ + ": Unexpected empty object: device_str")
            return False

        try:
            post = {StraenKeys.ACTIVITY_ID_KEY: activity_id_str, StraenKeys.ACTIVITY_NAME_KEY: activty_name, StraenKeys.ACTIVITY_TIME_KEY: date_time, StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str, StraenKeys.ACTIVITY_VISIBILITY_KEY: "public", StraenKeys.ACTIVITY_LOCATIONS_KEY: []}
            self.activities_collection.insert(post)
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity(self, object_id):
        """Delete method for an activity, specified by the database object ID."""
        if object_id is None:
            self.log_error(MongoDatabase.delete_activity.__name__ + ": Unexpected empty object: object_id")
            return False

        try:
            activity_id_obj = ObjectId(object_id)
            self.activities_collection.delete_one({StraenKeys.DATABASE_ID_KEY: activity_id_obj})
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_visibility(self, device_str, activity_id_str):
        """Returns the visibility setting for the specified activity."""
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_activity_visibility.__name__ + ": Unexpected empty object: device_str")
            return None
        if activity_id_str is None:
            self.log_error(MongoDatabase.retrieve_activity_visibility.__name__ + ": Unexpected empty object: activity_id_str")
            return None

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str, StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is not None:
                if StraenKeys.ACTIVITY_VISIBILITY_KEY in activity:
                    visibility = activity[StraenKeys.ACTIVITY_VISIBILITY_KEY]
                    return visibility
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def update_activity_visibility(self, activity_id_str, visibility):
        """Changes the visibility setting for the specified activity."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if visibility is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + ": Unexpected empty object: visibility")
            return False

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                activity[StraenKeys.ACTIVITY_VISIBILITY_KEY] = visibility
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_comment(self, device_str, activity_id_str, commenter_id, comment):
        """Create method for a comment on an activity."""
        if device_str is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id_str is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if commenter_id is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: commenter_id")
            return False
        if comment is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: comment")
            return False

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str, StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is not None:
                data = activity[StraenKeys.ACTIVITY_COMMENTS_KEY]
                data.append({commenter_id, comment})
                activity[StraenKeys.ACTIVITY_COMMENTS_KEY] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_metadata(self, activity_id_str, date_time, key, value, create_list):
        """Create method for a piece of metaadata."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: date_time")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: key")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: value")
            return False
        if create_list is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: value")
            return False

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:

                # The metadata is a list.
                if create_list is True:
                    data = []
                    if key in activity:
                        data = activity[key]

                        # Make sure time values are monotonically increasing.
                        if data and int(data[-1].keys()[0]) >= date_time:
                            self.log_error(MongoDatabase.create_metadata.__name__ + ": Received out-of-order time value.")
                            return False

                    value = {str(date_time): str(value)}
                    data.append(value)
                    activity[key] = data
                    self.activities_collection.save(activity)

                # The metadata is a scalar, just make sure it hasn't changed before updating it.
                elif key not in activity or activity[key] != value:
                    activity[key] = value
                    self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_metadata(self, key, activity_id_str):
        """Returns all the metadata for the specified sensor for the given activity."""
        if key is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + ": Unexpected empty object: key")
            return None
        if activity_id_str is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + ": Unexpected empty object: activity_id_str")
            return None

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                if key in activity:
                    metadata = activity[key]
                    if isinstance(metadata, list):
                        metadata.sort(key=retrieve_time_from_time_value_pair)
                    return metadata
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_sensordata(self, activity_id_str, date_time, sensor_type, value):
        """Create method for a piece of sensor data, such as a heart rate or power meter reading."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + ": Unexpected empty object: date_time")
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + ": Unexpected empty object: sensor_type")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + ": Unexpected empty object: value")
            return False

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                data = []
                if sensor_type in activity:
                    data = activity[sensor_type]

                    # Make sure time values are monotonically increasing.
                    if data and int(data[-1].keys()[0]) >= date_time:
                        self.log_error(MongoDatabase.create_sensordata.__name__ + ": Received out-of-order time value.")
                        return False

                value = {str(date_time): str(value)}
                data.append(value)
                activity[sensor_type] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_sensordata(self, sensor_type, activity_id_str):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if sensor_type is None:
            self.log_error(MongoDatabase.retrieve_sensordata.__name__ + ": Unexpected empty object: sensor_type")
            return None
        if activity_id_str is None:
            self.log_error(MongoDatabase.retrieve_sensordata.__name__ + ": Unexpected empty object: activity_id_str")
            return None

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                if sensor_type in activity:
                    sensor_data = activity[sensor_type]
                    sensor_data.sort(key=retrieve_time_from_time_value_pair)
                    return sensor_data
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_location(self, device_str, activity_id_str, date_time, latitude, longitude, altitude):
        """Create method for a location."""
        if device_str is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id_str is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if latitude is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: latitude")
            return False
        if longitude is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: longitude")
            return False
        if altitude is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: altitude")
            return False

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str, StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is None:
                if self.create_activity(activity_id_str, "", date_time / 1000, device_str):
                    activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str, StraenKeys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is not None:
                location_list = []

                if StraenKeys.ACTIVITY_LOCATIONS_KEY in activity:
                    location_list = activity[StraenKeys.ACTIVITY_LOCATIONS_KEY]

                    # Make sure time values are monotonically increasing.
                    if location_list and int(location_list[-1][StraenKeys.LOCATION_TIME_KEY]) >= date_time:
                        self.log_error(MongoDatabase.create_location.__name__ + ": Received out-of-order time value.")
                        return False

                value = {StraenKeys.LOCATION_TIME_KEY: date_time, StraenKeys.LOCATION_LAT_KEY: latitude, StraenKeys.LOCATION_LON_KEY: longitude, StraenKeys.LOCATION_ALT_KEY: altitude}
                location_list.append(value)
                activity[StraenKeys.ACTIVITY_LOCATIONS_KEY] = location_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_sensor_reading(self, device_str, activity_id_str, date_time, key, value):
        """Inherited from LocationWriter. Processes a sensor reading from the importer."""
        pass

    def retrieve_locations(self, activity_id_str):
        """Returns all the locations for the specified activity."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.retrieve_locations.__name__ + ": Unexpected empty object: activity_id_str")
            return None

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                locations = activity[StraenKeys.ACTIVITY_LOCATIONS_KEY]
                locations.sort(key=retrieve_time_from_location)
                return locations
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_most_recent_locations(self, activity_id_str, num):
        """Returns the most recent 'num' locations for the specified activity."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + ": Unexpected empty object: activity_id_str")
            return None
        if num is None:
            self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + ": Unexpected empty object: num")
            return None

        try:
            locations = self.retrieve_locations(activity_id_str)
            locations.sort(key=retrieve_time_from_location)
            return locations
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_tag(self, activity_id_str, tag):
        """Adds a tag to the specified activity."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: activity_id_str")
            return False
        if tag is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: tag")
            return False

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                data = []
                if StraenKeys.ACTIVITY_TAGS_KEY in activity:
                    data = activity[StraenKeys.ACTIVITY_TAGS_KEY]
                data.append(tag)
                activity[StraenKeys.ACTIVITY_TAGS_KEY] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_tags(self, activity_id_str):
        """Retrieves all the tags for the specified activity."""
        if activity_id_str is None:
            self.log_error(MongoDatabase.retrieve_tags.__name__ + ": Unexpected empty object: activity_id_str")
            return None

        try:
            activity = self.activities_collection.find_one({StraenKeys.ACTIVITY_ID_KEY: activity_id_str})
            if activity is not None:
                tags = activity[StraenKeys.ACTIVITY_TAGS_KEY]
                return tags
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None
