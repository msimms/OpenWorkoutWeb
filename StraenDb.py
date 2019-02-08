# Copyright 2017 Michael J Simms
"""Database implementation"""

import json
import re
import sys
import traceback
from bson.objectid import ObjectId
import pymongo
import Database
import InputChecker
import Keys


def retrieve_time_from_accelerometer_reading(location):
    """Used with the sort function."""
    return location['time']

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
            self.records_collection = self.database['records']
            self.workouts_collection = self.database['wokrouts']
            self.gear_collection = self.database['gear']
            return True
        except pymongo.errors.ConnectionFailure, e:
            self.log_error("Could not connect to MongoDB: %s" % e)
        return False

    def total_users_count(self):
        """Returns the number of users in the database."""
        try:
            return self.users_collection.count()
        except:
            self.log_error(MongoDatabase.total_users_count.__name__ + ": Exception")
        return 0

    def total_activities_count(self):
        """Returns the number of activities in the database."""
        try:
            return self.activities_collection.count()
        except:
            self.log_error(MongoDatabase.total_activities_count.__name__ + ": Exception")
        return 0

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
            post = {Keys.USERNAME_KEY: username, Keys.REALNAME_KEY: realname, Keys.HASH_KEY: passhash, Keys.DEVICES_KEY: [], Keys.FOLLOWING_KEY: [], Keys.DEFAULT_PRIVACY: Keys.ACTIVITY_VISIBILITY_PUBLIC}
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
            user = self.users_collection.find_one({Keys.USERNAME_KEY: username})
            if user is not None:
                return str(user[Keys.DATABASE_ID_KEY]), user[Keys.HASH_KEY], user[Keys.REALNAME_KEY]
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                return user[Keys.USERNAME_KEY], user[Keys.REALNAME_KEY]
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                user[Keys.USERNAME_KEY] = username
                user[Keys.REALNAME_KEY] = realname
                if passhash is not None:
                    user[Keys.HASH_KEY] = passhash
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
            user = self.users_collection.delete_one({Keys.DATABASE_ID_KEY: user_id_obj})
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
            matched_users = self.users_collection.find({Keys.USERNAME_KEY: {"$regex": username}})
            if matched_users is not None:
                for matched_user in matched_users:
                    user_list.append(matched_user[Keys.USERNAME_KEY])
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            devices = []
            if user is not None:
                if Keys.DEVICES_KEY in user:
                    devices = user[Keys.DEVICES_KEY]
            if device_str not in devices:
                devices.append(device_str)
                user[Keys.DEVICES_KEY] = devices
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                if Keys.DEVICES_KEY in user:
                    return user[Keys.DEVICES_KEY]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user_from_device(self, device_str):
        """Finds the user associated with the device."""
        if len(device_str) == 0:
            return False, "Device string not provided."

        try:
            return self.users_collection.find_one({Keys.DEVICES_KEY: device_str})
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
            self.activities_collection.remove({Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                if Keys.FOLLOWING_KEY in user:
                    following_ids = user[Keys.FOLLOWING_KEY]
                    following_users = []
                    for following_id in following_ids:
                        username, realname = self.retrieve_user_from_id(following_id)
                        user = {}
                        user[Keys.DATABASE_ID_KEY] = following_id
                        user[Keys.USERNAME_KEY] = username
                        user[Keys.REALNAME_KEY] = realname
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
            followers = self.users_collection.find({Keys.FOLLOWING_KEY: user_id})
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                user_list = []
                if Keys.FOLLOWING_KEY in user:
                    user_list = user[Keys.FOLLOWING_KEY]
                if target_id not in user_list:
                    user_list.append(target_id)
                    user[Keys.FOLLOWING_KEY] = user_list
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
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
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                if key in user:
                    return user[key]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_user_personal_records(self, user_id, records):
        """Create method for a user's personal record."""
        if user_id is None:
            self.log_error(MongoDatabase.create_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return False
        if records is None:
            self.log_error(MongoDatabase.create_user_personal_records.__name__ + ": Unexpected empty object: records")
            return False

        try:
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is None:
                post = {Keys.RECORDS_USER_ID: user_id, Keys.PERSONAL_RECORDS: records}
                self.records_collection.insert(post)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user_personal_records(self, user_id):
        """Retrieve method for a user's personal records."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return {}

        try:
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                if Keys.PERSONAL_RECORDS in user_records:
                    return user_records[Keys.PERSONAL_RECORDS]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return {}

    def update_user_personal_records(self, user_id, records):
        """Create method for a user's personal record."""
        if user_id is None:
            self.log_error(MongoDatabase.update_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return False
        if records is None or len(records) == 0:
            self.log_error(MongoDatabase.update_user_personal_records.__name__ + ": Unexpected empty object: records")
            return False

        try:
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                user_records[Keys.PERSONAL_RECORDS] = records
                self.records_collection.save(user_records)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_bests(self, user_id, activity_id, activity_type, activity_time, bests):
        """Create method for a user's personal records for a given activity."""
        if user_id is None:
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: user_id")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: activity_id")
            return False
        if activity_type is None:
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: activity_type")
            return False
        if activity_time is None:
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: activity_time")
            return False
        if bests is None:
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: bests")
            return False

        try:
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                bests[Keys.ACTIVITY_TYPE_KEY] = activity_type
                bests[Keys.ACTIVITY_TIME_KEY] = activity_time
                user_records[activity_id] = bests
                self.records_collection.save(user_records)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_bests_for_user(self, user_id):
        """Retrieve method for a user's activity records."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_activity_bests_for_user.__name__ + ": Unexpected empty object: user_id")
            return {}

        try:
            bests = {}
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                for record in user_records:
                    if InputChecker.is_uuid(record):
                        bests[record] = user_records[record]
                return bests
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return {}

    def retrieve_recent_activity_bests_for_user(self, user_id, cutoff_time):
        """Retrieve method for a user's activity records. Only activities more recent than the specified cutoff time will be returned."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_recent_activity_bests_for_user.__name__ + ": Unexpected empty object: user_id")
            return {}

        try:
            bests = {}
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                for record in user_records:
                    if InputChecker.is_uuid(record):
                        records = user_records[record]
                        if records[Keys.ACTIVITY_TIME_KEY] > cutoff_time:
                            bests[record] = records
                return bests
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return {}

    def list_excluded_keys(self):
        """This is the list of stuff we don't need to return when we're building an activity list. Helps with efficiency."""
        exclude_keys = {}
        exclude_keys[Keys.APP_CADENCE_KEY] = False
        exclude_keys[Keys.APP_CURRENT_SPEED_KEY] = False
        exclude_keys[Keys.APP_AVG_SPEED_KEY] = False
        exclude_keys[Keys.APP_MOVING_SPEED_KEY] = False
        exclude_keys[Keys.APP_HEART_RATE_KEY] = False
        exclude_keys[Keys.APP_AVG_HEART_RATE_KEY] = False
        exclude_keys[Keys.APP_CURRENT_PACE_KEY] = False
        exclude_keys[Keys.APP_POWER_KEY] = False
        exclude_keys[Keys.ACTIVITY_LOCATIONS_KEY] = False
        return exclude_keys

    def retrieve_user_activity_list(self, user_id, start, num_results, exclude_keys):
        """Retrieves the list of activities associated with the specified user."""
        if num_results is not None and num_results <= 0:
            return None

        try:
            if start is None and num_results is None:
                return list(self.activities_collection.find({Keys.ACTIVITY_USER_ID_KEY: user_id}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1))
            elif num_results is None:
                return list(self.activities_collection.find({Keys.ACTIVITY_USER_ID_KEY: user_id}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1).skip(start))
            else:
                return list(self.activities_collection.find({Keys.ACTIVITY_USER_ID_KEY: user_id}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1).skip(start).limit(num_results))
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_each_user_activity(self, context, user_id, callback_func):
        """Retrieves each user activity and calls the callback function for each one."""
        try:
            activities = self.activities_collection.find({Keys.ACTIVITY_USER_ID_KEY: user_id})
            for activity in activities:
                callback_func(context, activity, user_id)
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
            exclude_keys = self.list_excluded_keys()

            if start is None and num_results is None:
                return list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1))
            elif num_results is None:
                return list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1).skip(start))
            else:
                return list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1).skip(start).limit(num_results))
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
            device_activities = self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}).sort(Keys.DATABASE_ID_KEY, -1).limit(1)
            if device_activities is not None and device_activities.count() > 0:
                activity = device_activities.next()
                return activity
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity(self, activity_id, activty_name, date_time, device_str):
        """Create method for an activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity.__name__ + ": Unexpected empty object: activity_id")
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
            post = {Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_NAME_KEY: activty_name, Keys.ACTIVITY_TIME_KEY: date_time, Keys.ACTIVITY_DEVICE_STR_KEY: device_str, Keys.ACTIVITY_VISIBILITY_KEY: "public", Keys.ACTIVITY_LOCATIONS_KEY: []}
            self.activities_collection.insert(post)
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity(self, activity_id):
        """Retrieve method for an activity, specified by the activity ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            return self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: re.compile(activity_id, re.IGNORECASE)})
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def delete_activity(self, object_id):
        """Delete method for an activity, specified by the database object ID."""
        if object_id is None:
            self.log_error(MongoDatabase.delete_activity.__name__ + ": Unexpected empty object: object_id")
            return False

        try:
            activity_id_obj = ObjectId(object_id)
            self.activities_collection.delete_one({Keys.DATABASE_ID_KEY: activity_id_obj})
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_visibility(self, activity_id):
        """Returns the visibility setting for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_visibility.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if Keys.ACTIVITY_VISIBILITY_KEY in activity:
                    visibility = activity[Keys.ACTIVITY_VISIBILITY_KEY]
                    return visibility
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def update_activity_visibility(self, activity_id, visibility):
        """Changes the visibility setting for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + ": Unexpected empty object: activity_id")
            return False
        if visibility is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + ": Unexpected empty object: visibility")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                activity[Keys.ACTIVITY_VISIBILITY_KEY] = visibility
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Create method for a location."""
        if device_str is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_location.__name__ + ": Unexpected empty object: activity_id")
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
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is None:
                if self.create_activity(activity_id, "", date_time / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is not None:
                location_list = []

                if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                    location_list = activity[Keys.ACTIVITY_LOCATIONS_KEY]

                value = {Keys.LOCATION_TIME_KEY: date_time, Keys.LOCATION_LAT_KEY: latitude, Keys.LOCATION_LON_KEY: longitude, Keys.LOCATION_ALT_KEY: altitude}
                location_list.append(value)
                location_list.sort(key=retrieve_time_from_location)
                activity[Keys.ACTIVITY_LOCATIONS_KEY] = location_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_locations(self, device_str, activity_id, locations):
        """Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        if device_str is None:
            self.log_error(MongoDatabase.create_locations.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_locations.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not locations:
            self.log_error(MongoDatabase.create_locations.__name__ + ": Unexpected empty object: locations")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is None:
                first_location = locations[0]
                if self.create_activity(activity_id, "", first_location[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is not None:
                location_list = []

                if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                    location_list = activity[Keys.ACTIVITY_LOCATIONS_KEY]

                for location in locations:
                    value = {Keys.LOCATION_TIME_KEY: location[0], Keys.LOCATION_LAT_KEY: location[1], Keys.LOCATION_LON_KEY: location[2], Keys.LOCATION_ALT_KEY: location[3]}
                    location_list.append(value)

                location_list.sort(key=retrieve_time_from_location)
                activity[Keys.ACTIVITY_LOCATIONS_KEY] = location_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_locations(self, activity_id):
        """Returns all the locations for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_locations.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                    locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
                    locations.sort(key=retrieve_time_from_location)
                    return locations
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_most_recent_locations(self, activity_id, num):
        """Returns the most recent 'num' locations for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + ": Unexpected empty object: activity_id")
            return None
        if num is None:
            self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + ": Unexpected empty object: num")
            return None

        try:
            locations = self.retrieve_locations(activity_id)
            locations.sort(key=retrieve_time_from_location)
            return locations
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Create method for a piece of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: activity_id")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: date_time")
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: sensor_type")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: value")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                value_list = []

                if sensor_type in activity:
                    value_list = activity[sensor_type]

                time_value_pair = {str(date_time): float(value)}
                value_list.append(time_value_pair)
                value_list.sort(key=retrieve_time_from_time_value_pair)
                activity[sensor_type] = value_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_sensor_readings(self, activity_id, sensor_type, values):
        """Create method for several pieces of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: activity_id")
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: sensor_type")
            return False
        if values is None:
            self.log_error(MongoDatabase.create_sensor_reading.__name__ + ": Unexpected empty object: values")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                value_list = []

                if sensor_type in activity:
                    value_list = activity[sensor_type]

                for value in values:
                    time_value_pair = {str(value[0]): float(value[1])}
                    value_list.append(time_value_pair)

                value_list.sort(key=retrieve_time_from_time_value_pair)
                activity[sensor_type] = value_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_sensor_readings(self, sensor_type, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if sensor_type is None:
            self.log_error(MongoDatabase.retrieve_sensor_readings.__name__ + ": Unexpected empty object: sensor_type")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_sensor_readings.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if sensor_type in activity:
                    sensor_data = activity[sensor_type]
                    sensor_data.sort(key=retrieve_time_from_time_value_pair)
                    return sensor_data
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for a piece of metaadata."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: activity_id")
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
            self.log_error(MongoDatabase.create_metadata.__name__ + ": Unexpected empty object: create_list")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:

                # Make sure we're working with a number, if the value is supposed to be a number.
                try:
                    value = float(value)
                except ValueError:
                    pass

                # The metadata is a list.
                if create_list is True:
                    value_list = []

                    if key in activity:
                        value_list = activity[key]

                    time_value_pair = {str(date_time): value}
                    value_list.append(time_value_pair)
                    value_list.sort(key=retrieve_time_from_time_value_pair)
                    activity[key] = value_list
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

    def create_metadata_list(self, activity_id, key, values):
        """Create method for a list of of metaadata values."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_metadata_list.__name__ + ": Unexpected empty object: activity_id")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_metadata_list.__name__ + ": Unexpected empty object: key")
            return False
        if values is None:
            self.log_error(MongoDatabase.create_metadata_list.__name__ + ": Unexpected empty object: values")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                value_list = []

                if key in activity:
                    value_list = activity[key]

                for value in values:
                    time_value_pair = {str(value[0]): float(value[1])}
                    value_list.append(time_value_pair)

                value_list.sort(key=retrieve_time_from_time_value_pair)
                activity[key] = value_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False
        
    def retrieve_metadata(self, key, activity_id):
        """Returns all the metadata of the given type for the specified activity."""
        if key is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + ": Unexpected empty object: key")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
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

    def create_sets_and_reps_data(self, activity_id, sets):
        """Create method for a list of of metaadata values."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_sets_and_reps_data.__name__ + ": Unexpected empty object: activity_id")
            return False
        if sets is None:
            self.log_error(MongoDatabase.create_sets_and_reps_data.__name__ + ": Unexpected empty object: sets")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                activity[Keys.APP_SETS_KEY] = sets
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_accelerometer_reading(self, device_str, activity_id, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if device_str is None:
            self.log_error(MongoDatabase.create_accelerometer_reading.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_accelerometer_reading.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not accels:
            self.log_error(MongoDatabase.create_accelerometer_reading.__name__ + ": Unexpected empty object: accels")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is None:
                first_accel = accels[0]
                if self.create_activity(activity_id, "", first_accel[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})
            if activity is not None:
                accel_list = []
                if Keys.APP_ACCELEROMETER_KEY in activity:
                    accel_list = activity[Keys.APP_ACCELEROMETER_KEY]
                for accel in accels:
                    # Make sure time values are monotonically increasing.
                    if accel_list and int(accel_list[-1][Keys.ACCELEROMETER_TIME_KEY]) > accel[0]:
                        self.log_error(MongoDatabase.create_accelerometer_reading.__name__ + ": Received out-of-order time value.")
                    else:
                        value = {Keys.ACCELEROMETER_TIME_KEY: accel[0], Keys.ACCELEROMETER_AXIS_NAME_X: accel[1], Keys.ACCELEROMETER_AXIS_NAME_Y: accel[2], Keys.ACCELEROMETER_AXIS_NAME_Z: accel[3]}
                        accel_list.append(value)

                activity[Keys.APP_ACCELEROMETER_KEY] = accel_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_accelerometer_readings(self, activity_id):
        """Returns all the locations for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_accelerometer_readings.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if Keys.APP_ACCELEROMETER_KEY in activity:
                    accels = activity[Keys.APP_ACCELEROMETER_KEY]
                    accels.sort(key=retrieve_time_from_accelerometer_reading)
                    return accels
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity_summary(self, activity_id, summary_data):
        """Create method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return False
        if summary_data is None:
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Unexpected empty object: summary_data")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                activity[Keys.ACTIVITY_SUMMARY_KEY] = summary_data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_summary(self, activity_id):
        """Returns the activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if Keys.ACTIVITY_SUMMARY_KEY in activity:
                    summary_data = activity[Keys.ACTIVITY_SUMMARY_KEY]
                    return summary_data
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def delete_activity_summary(self, activity_id):
        """Delete method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.delete_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                pass
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_tag(self, activity_id, tag):
        """Adds a tag to the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: activity_id")
            return False
        if tag is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: tag")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                data = []
                if Keys.ACTIVITY_TAGS_KEY in activity:
                    data = activity[Keys.ACTIVITY_TAGS_KEY]
                data.append(tag)
                activity[Keys.ACTIVITY_TAGS_KEY] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_tags(self, activity_id):
        """Retrieves all the tags for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_tags.__name__ + ": Unexpected empty object: activity_id")
            return []

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if Keys.ACTIVITY_TAGS_KEY in activity:
                    return activity[Keys.ACTIVITY_TAGS_KEY]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return []

    def delete_tag(self, activity_id, tag):
        """Deletes the specified tag from the activity with the given ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: activity_id")
            return False
        if tag is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: tag")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                data = []
                if Keys.ACTIVITY_TAGS_KEY in activity:
                    data = activity[Keys.ACTIVITY_TAGS_KEY]
                    data.remove(tag)
                    activity[Keys.ACTIVITY_TAGS_KEY] = data
                    self.activities_collection.save(activity)
                    return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_comment(self, activity_id, commenter_id, comment):
        """Create method for a comment on an activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: activity_id")
            return False
        if commenter_id is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: commenter_id")
            return False
        if comment is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: comment")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                data = []
                if Keys.ACTIVITY_COMMENTS_KEY in activity:
                    data = activity[Keys.ACTIVITY_COMMENTS_KEY]
                entry_dict = {Keys.ACTIVITY_COMMENTER_ID_KEY: commenter_id, Keys.ACTIVITY_COMMENT_KEY: comment}
                entry_str = json.dumps(entry_dict)
                data.append(entry_str)
                activity[Keys.ACTIVITY_COMMENTS_KEY] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_comments(self, activity_id):
        """Returns a list containing all of the comments on the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_comments.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})
            if activity is not None:
                if Keys.ACTIVITY_COMMENTS_KEY in activity:
                    return activity[Keys.ACTIVITY_COMMENTS_KEY]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_workout(self, user_id):
        """Create method for a workout."""
        if user_id is None:
            self.log_error(MongoDatabase.create_workout.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            pass
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return True

    def retrieve_workout(self, workout_id):
        """Retrieve method for the workout with the specified ID."""
        if workout_id is None:
            self.log_error(MongoDatabase.retrieve_workout.__name__ + ": Unexpected empty object: workout_id")
            return None

        try:
            pass
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def delete_workout(self, workout_id):
        """Delete method for the workout with the specified ID."""
        if workout_id is None:
            self.log_error(MongoDatabase.delete_workout.__name__ + ": Unexpected empty object: workout_id")
            return False

        try:
            workout_id_obj = ObjectId(workout_id)
            workout = self.workouts_collection.delete_one({Keys.DATABASE_ID_KEY: workout_id_obj})
            if workout is not None:
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_gear(self, user_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Create method for gear."""
        if user_id is None:
            self.log_error(MongoDatabase.create_gear.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return True

    def retrieve_gear_for_user(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_gear_for_user.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                gear_list = []
                if Keys.GEAR_KEY in user:
                    pass
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return []

    def update_gear(self, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Retrieve method for the gear with the specified ID."""
        if gear_id is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: gear_id")
            return False

        try:
            gear_id_obj = ObjectId(gear_id)
            gear = self.gear_collection.find_one({Keys.DATABASE_ID_KEY: gear_id_obj})
            if gear is not None:
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def delete_gear(self, user_id, gear_id):
        """Delete method for the gear with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_gear.__name__ + ": Unexpected empty object: user_id")
            return None
        if gear_id is None:
            self.log_error(MongoDatabase.delete_gear.__name__ + ": Unexpected empty object: gear_id")
            return False

        try:
            gear_id_obj = ObjectId(gear_id)
            gear = self.gear_collection.delete_one({Keys.DATABASE_ID_KEY: gear_id_obj})
            if gear is not None:
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False
