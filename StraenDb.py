# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2017 Mike Simms
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
"""Database implementation"""

import json
import re
import sys
import traceback
import uuid
from bson.objectid import ObjectId
import pymongo
import time
import Database
import InputChecker
import Keys
import Workout


def retrieve_time_from_location(location):
    """Used with the sort function."""
    return location['time']

def retrieve_time_from_time_value_pair(value):
    """Used with the sort function."""
    if sys.version_info[0] < 3:
        return value.keys()[0]
    return list(value.keys())[0]


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
    workouts_collection = None
    tasks_collectoin = None

    def __init__(self):
        Database.Database.__init__(self)

    def connect(self):
        """Connects/creates the database"""
        try:
            self.conn = pymongo.MongoClient('localhost:27017')
            self.database = self.conn['straendb']
            self.users_collection = self.database['users']
            self.activities_collection = self.database['activities']
            self.records_collection = self.database['records']
            self.workouts_collection = self.database['workouts']
            self.tasks_collection = self.database['tasks']
            return True
        except pymongo.errors.ConnectionFailure as e:
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

    def list_excluded_activity_keys(self):
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

    def list_excluded_user_keys(self):
        """This is the list of stuff we don't need to return when we're building a friends list. Helps with efficiency and privacy by not exposing more than we need."""
        exclude_keys = {}
        exclude_keys[Keys.HASH_KEY] = False
        exclude_keys[Keys.DEVICES_KEY] = False
        exclude_keys[Keys.FRIEND_REQUESTS_KEY] = False
        exclude_keys[Keys.FRIENDS_KEY] = False
        exclude_keys[Keys.PR_KEY] = False
        exclude_keys[Keys.DEFAULT_PRIVACY] = False
        exclude_keys[Keys.PREFERRED_UNITS_KEY] = False
        return exclude_keys

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
            post = {Keys.USERNAME_KEY: username, Keys.REALNAME_KEY: realname, Keys.HASH_KEY: passhash, Keys.DEVICES_KEY: [], Keys.FRIENDS_KEY: [], Keys.DEFAULT_PRIVACY: Keys.ACTIVITY_VISIBILITY_PUBLIC}
            self.users_collection.insert(post)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user_details(self, username):
        """Retrieve method for a user."""
        if username is None:
            self.log_error(MongoDatabase.retrieve_user_details.__name__ + ": Unexpected empty object: username")
            return None
        if len(username) == 0:
            self.log_error(MongoDatabase.retrieve_user_details.__name__ + ": username is empty")
            return None

        try:
            return self.users_collection.find_one({Keys.USERNAME_KEY: username})
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None, None, None

    def retrieve_user_from_id(self, user_id):
        """Retrieve method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_from_id.__name__ + ": Unexpected empty object: user_id")
            return None, None

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                return user[Keys.USERNAME_KEY], user[Keys.REALNAME_KEY]
            return None, None
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if user is not None:
                user[Keys.USERNAME_KEY] = username
                user[Keys.REALNAME_KEY] = realname
                if passhash is not None:
                    user[Keys.HASH_KEY] = passhash
                self.users_collection.save(user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_user(self, user_id):
        """Delete method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_user.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            user_id_obj = ObjectId(str(user_id))
            deleted_result = self.users_collection.delete_one({Keys.DATABASE_ID_KEY: user_id_obj})
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
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
            matched_usernames = self.users_collection.find({Keys.USERNAME_KEY: {"$regex": username}})
            if matched_usernames is not None:
                for matched_user in matched_usernames:
                    user_list.append(matched_user[Keys.USERNAME_KEY])
            matched_realnames = self.users_collection.find({Keys.REALNAME_KEY: {"$regex": username}})
            if matched_realnames is not None:
                for matched_user in matched_realnames:
                    username = matched_user[Keys.USERNAME_KEY]
                    if username not in user_list:
                        user_list.append(username)
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # Read the devices list.
            devices = []
            if user is not None and Keys.DEVICES_KEY in user:
                devices = user[Keys.DEVICES_KEY]

            # Append the device to the devices list, if it is not already there.
            if device_str not in devices:
                devices.append(device_str)
                user[Keys.DEVICES_KEY] = devices
                self.users_collection.save(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return True

    def retrieve_user_devices(self, user_id):
        """Retrieve method for a device."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_devices.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # Read the devices list.
            if user is not None and Keys.DEVICES_KEY in user:
                return user[Keys.DEVICES_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user_from_device(self, device_str):
        """Finds the user associated with the device."""
        if len(device_str) == 0:
            return False, "Device string not provided."

        try:
            return self.users_collection.find_one({Keys.DEVICES_KEY: device_str})
        except:
            self.log_error(traceback.format_exc())
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_pending_friend_request(self, user_id, target_id):
        """Appends a user to the friends list of the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.create_pending_friend_request.__name__ + ": Unexpected empty object: user_id")
            return None
        if target_id is None:
            self.log_error(MongoDatabase.create_pending_friend_request.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user whose friendship is being requested.
            user_id_obj = ObjectId(str(target_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user was found then add the target user to the pending friends list.
            if user is not None:
                pending_friends_list = []
                if Keys.FRIEND_REQUESTS_KEY in user:
                    pending_friends_list = user[Keys.FRIEND_REQUESTS_KEY]
                if user_id not in pending_friends_list:
                    pending_friends_list.append(user_id)
                    user[Keys.FRIEND_REQUESTS_KEY] = pending_friends_list
                    self.users_collection.save(user)
                    return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_pending_friends(self, user_id):
        """Returns the user ids for all users that are pending confirmation as friends of the specified user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_pending_friends.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Things we don't need.
            exclude_keys = self.list_excluded_user_keys()

            # Find the users whose friendship we have requested.
            pending_friends_list = []
            pending_friends = self.users_collection.find({Keys.FRIEND_REQUESTS_KEY: user_id}, exclude_keys)
            for pending_friend in pending_friends:
                pending_friend[Keys.DATABASE_ID_KEY] = str(pending_friend[Keys.DATABASE_ID_KEY])
                pending_friend[Keys.REQUESTING_USER_KEY] = "self"
                pending_friends_list.append(pending_friend)

            # Find the users who have requested our friendship.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If we found ourselves.
            if user is not None:
                temp_friend_id_list = []
                if Keys.FRIEND_REQUESTS_KEY in user:
                    temp_friend_id_list = user[Keys.FRIEND_REQUESTS_KEY]
                for temp_friend_id in temp_friend_id_list:
                    temp_friend_id_obj = ObjectId(str(temp_friend_id))
                    pending_friend = self.users_collection.find_one({Keys.DATABASE_ID_KEY: temp_friend_id_obj}, exclude_keys)
                    if pending_friend is not None:
                        pending_friend[Keys.DATABASE_ID_KEY] = str(pending_friend[Keys.DATABASE_ID_KEY])
                        pending_friend[Keys.REQUESTING_USER_KEY] = str(pending_friend[Keys.DATABASE_ID_KEY])
                        pending_friends_list.append(pending_friend)

            return pending_friends_list
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def delete_pending_friend_request(self, user_id, target_id):
        """Appends a user to the friends list of the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_pending_friend_request.__name__ + ": Unexpected empty object: user_id")
            return None
        if target_id is None:
            self.log_error(MongoDatabase.delete_pending_friend_request.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user whose friendship is being requested.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user was found then add the target user to the pending friends list.
            if user is not None:
                pending_friends_list = []
                if Keys.FRIEND_REQUESTS_KEY in user:
                    pending_friends_list = user[Keys.FRIEND_REQUESTS_KEY]
                if target_id in pending_friends_list:
                    pending_friends_list.remove(target_id)
                    user[Keys.FRIEND_REQUESTS_KEY] = pending_friends_list
                    self.users_collection.save(user)
                    return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_friend(self, user_id, target_id):
        """Appends a user to the friends list of the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.create_friend.__name__ + ": Unexpected empty object: user_id")
            return None
        if target_id is None:
            self.log_error(MongoDatabase.create_friend.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # Find the target user.
            target_user_id_obj = ObjectId(str(target_id))
            target_user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: target_user_id_obj})

            # If the users were found then add each other to their friends lists.
            if user is not None and target_user is not None:

                # Update the user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in user:
                    friends_list = user[Keys.FRIENDS_KEY]
                if target_id not in friends_list:
                    friends_list.append(target_id)
                    user[Keys.FRIENDS_KEY] = friends_list
                    self.users_collection.save(user)

                # Update the target user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in target_user:
                    friends_list = target_user[Keys.FRIENDS_KEY]
                if user_id not in friends_list:
                    friends_list.append(user_id)
                    target_user[Keys.FRIENDS_KEY] = friends_list
                    self.users_collection.save(target_user)

                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_friends(self, user_id):
        """Returns the user ids for all users that are friends with the user who has the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_friends.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Things we don't need.
            exclude_keys = self.list_excluded_user_keys()

            friends_list = []
            friends = self.users_collection.find({Keys.FRIENDS_KEY: user_id}, exclude_keys)
            for friend in friends:
                friend[Keys.DATABASE_ID_KEY] = str(friend[Keys.DATABASE_ID_KEY])
                friends_list.append(friend)
            return friends_list
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def delete_friend(self, user_id, target_id):
        """Removes the users from each other's friends lists."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_friend.__name__ + ": Unexpected empty object: user_id")
            return None
        if target_id is None:
            self.log_error(MongoDatabase.delete_friend.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # Find the target user.
            target_user_id_obj = ObjectId(str(target_id))
            target_user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: target_user_id_obj})

            # If the users were found then add each other to their friends lists.
            if user is not None and target_user is not None:

                # Update the user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in user:
                    friends_list = user[Keys.FRIENDS_KEY]
                if target_id in friends_list:
                    friends_list.remove(target_id)
                    user[Keys.FRIENDS_KEY] = friends_list
                    self.users_collection.save(user)

                # Update the target user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in target_user:
                    friends_list = target_user[Keys.FRIENDS_KEY]
                if user_id in friends_list:
                    friends_list.remove(user_id)
                    target_user[Keys.FRIENDS_KEY] = friends_list
                    self.users_collection.save(target_user)

                return True
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user was found.
            if user is not None:
                user[key] = value
                self.users_collection.save(user)
                return True
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # Find the setting.
            if user is not None and key in user:
                return user[key]
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user's records collection.
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is None:
                post = {Keys.RECORDS_USER_ID: user_id, Keys.PERSONAL_RECORDS: records}
                self.records_collection.insert(post)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user_personal_records(self, user_id):
        """Retrieve method for a user's personal records."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return {}

        try:
            # Find the user's records collection.
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None and Keys.PERSONAL_RECORDS in user_records:
                return user_records[Keys.PERSONAL_RECORDS]
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user's records collection.
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                user_records[Keys.PERSONAL_RECORDS] = records
                self.records_collection.save(user_records)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_user_personal_records(self, user_id):
        """Create method for a user's personal record."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            # Delete the user's records collection.
            deleted_result = self.records_collection.delete_one({Keys.RECORDS_USER_ID: user_id})
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user's records collection.
            user_records = self.records_collection.find_one({Keys.RECORDS_USER_ID: user_id})
            if user_records is not None:
                bests[Keys.ACTIVITY_TYPE_KEY] = activity_type
                bests[Keys.ACTIVITY_TIME_KEY] = activity_time
                user_records[activity_id] = bests
                self.records_collection.save(user_records)
                return True
        except:
            self.log_error(traceback.format_exc())
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
            self.log_error(traceback.format_exc())
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
                        activity_bests = user_records[record]
                        if (cutoff_time is None) or (activity_bests[Keys.ACTIVITY_TIME_KEY] > cutoff_time):
                            bests[record] = activity_bests
                return bests
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return {}

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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_each_user_activity(self, context, user_id, callback_func):
        """Retrieves each user activity and calls the callback function for each one."""
        try:
            activities = list(self.activities_collection.find({Keys.ACTIVITY_USER_ID_KEY: user_id}))
            for activity in activities:
                callback_func(context, activity, user_id)
        except:
            self.log_error(traceback.format_exc())
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
            exclude_keys = self.list_excluded_activity_keys()

            if start is None and num_results is None:
                return list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1))
            elif num_results is None:
                return list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1).skip(start))
            else:
                return list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}, exclude_keys).sort(Keys.DATABASE_ID_KEY, -1).skip(start).limit(num_results))
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_each_device_activity(self, context, user_id, device_str, callback_func):
        """Retrieves each device activity and calls the callback function for each one."""
        try:
            activities = list(self.activities_collection.find({Keys.ACTIVITY_DEVICE_STR_KEY: device_str}))
            for activity in activities:
                callback_func(context, activity, user_id)
        except:
            self.log_error(traceback.format_exc())
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
            self.log_error(traceback.format_exc())
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity(self, activity_id):
        """Retrieve method for an activity, specified by the activity ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            # Find the activity.
            return self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: re.compile(activity_id, re.IGNORECASE)})
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def update_activity(self, device_str, activity_id, locations, sensor_readings_dict, metadata_list_dict):
        """Updates locations, sensor readings, and metadata associated with a moving activity. Provided as a performance improvement over making several database updates."""
        if device_str is None:
            self.log_error(MongoDatabase.update_activity.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.update_activity.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not locations:
            self.log_error(MongoDatabase.update_activity.__name__ + ": Unexpected empty object: locations")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was not found then create it.
            if activity is None:
                first_location = locations[0]
                if self.create_activity(activity_id, "", first_location[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was found.
            if activity is not None:

                # Update the locations.
                location_list = []
                if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                    location_list = activity[Keys.ACTIVITY_LOCATIONS_KEY]
                for location in locations:
                    value = {Keys.LOCATION_TIME_KEY: location[0], Keys.LOCATION_LAT_KEY: location[1], Keys.LOCATION_LON_KEY: location[2], Keys.LOCATION_ALT_KEY: location[3]}
                    location_list.append(value)
                location_list.sort(key=retrieve_time_from_location)
                activity[Keys.ACTIVITY_LOCATIONS_KEY] = location_list

                # Update the sensor readings.
                if sensor_readings_dict:
                    for sensor_type in sensor_readings_dict:
                        value_list = []
                        if sensor_type in activity:
                            value_list = activity[sensor_type]
                        for value in sensor_readings_dict[sensor_type]:
                            time_value_pair = {str(value[0]): float(value[1])}
                            value_list.append(time_value_pair)
                        value_list.sort(key=retrieve_time_from_time_value_pair)
                        activity[sensor_type] = value_list

                # Update the metadata readings.
                if metadata_list_dict:
                    for metadata_type in metadata_list_dict:
                        value_list = []
                        if metadata_type in activity:
                            value_list = activity[metadata_type]
                        for value in metadata_list_dict[metadata_type]:
                            time_value_pair = {str(value[0]): float(value[1])}
                            value_list.append(time_value_pair)
                        value_list.sort(key=retrieve_time_from_time_value_pair)
                        activity[metadata_type] = value_list

                # Write out the changes.
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity(self, object_id):
        """Delete method for an activity, specified by the database object ID."""
        if object_id is None:
            self.log_error(MongoDatabase.delete_activity.__name__ + ": Unexpected empty object: object_id")
            return False

        try:
            activity_id_obj = ObjectId(str(object_id))
            deleted_result = self.activities_collection.delete_one({Keys.DATABASE_ID_KEY: activity_id_obj})
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_visibility(self, activity_id):
        """Returns the visibility setting for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_visibility.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found and it has a visibility setting.
            if activity is not None and Keys.ACTIVITY_VISIBILITY_KEY in activity:
                visibility = activity[Keys.ACTIVITY_VISIBILITY_KEY]
                return visibility
        except:
            self.log_error(traceback.format_exc())
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
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None:
                activity[Keys.ACTIVITY_VISIBILITY_KEY] = visibility
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Create method for a location."""
        if device_str is None:
            self.log_error(MongoDatabase.create_activity_location.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_location.__name__ + ": Unexpected empty object: activity_id")
            return False
        if latitude is None:
            self.log_error(MongoDatabase.create_activity_location.__name__ + ": Unexpected empty object: latitude")
            return False
        if longitude is None:
            self.log_error(MongoDatabase.create_activity_location.__name__ + ": Unexpected empty object: longitude")
            return False
        if altitude is None:
            self.log_error(MongoDatabase.create_activity_location.__name__ + ": Unexpected empty object: altitude")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was not found then create it.
            if activity is None:
                if self.create_activity(activity_id, "", date_time / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was found.
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_locations(self, device_str, activity_id, locations):
        """Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        if device_str is None:
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not locations:
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Unexpected empty object: locations")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was not found then create it.
            if activity is None:
                first_location = locations[0]
                if self.create_activity(activity_id, "", first_location[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was found.
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_locations(self, activity_id):
        """Returns all the locations for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_locations.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found and it has location data.
            if activity is not None and Keys.ACTIVITY_LOCATIONS_KEY in activity:
                locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
                locations.sort(key=retrieve_time_from_location)
                return locations
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_most_recent_activity_locations(self, activity_id, num):
        """Returns the most recent 'num' locations for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_most_recent_activity_locations.__name__ + ": Unexpected empty object: activity_id")
            return None
        if num is None:
            self.log_error(MongoDatabase.retrieve_most_recent_activity_locations.__name__ + ": Unexpected empty object: num")
            return None

        try:
            locations = self.retrieve_activity_locations(activity_id)
            locations.sort(key=retrieve_time_from_location)
            return locations
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Create method for a piece of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_sensor_reading.__name__ + ": Unexpected empty object: activity_id")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_activity_sensor_reading.__name__ + ": Unexpected empty object: date_time")
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_activity_sensor_reading.__name__ + ": Unexpected empty object: sensor_type")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_activity_sensor_reading.__name__ + ": Unexpected empty object: value")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_sensor_readings(self, activity_id, sensor_type, values):
        """Create method for several pieces of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_sensor_readings.__name__ + ": Unexpected empty object: activity_id")
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_activity_sensor_readings.__name__ + ": Unexpected empty object: sensor_type")
            return False
        if values is None:
            self.log_error(MongoDatabase.create_activity_sensor_readings.__name__ + ": Unexpected empty object: values")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_sensor_readings(self, sensor_type, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if sensor_type is None:
            self.log_error(MongoDatabase.retrieve_activity_sensor_readings.__name__ + ": Unexpected empty object: sensor_type")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_sensor_readings.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found and if it has data for the specified sensor type.
            if activity is not None and sensor_type in activity:
                sensor_data = activity[sensor_type]
                sensor_data.sort(key=retrieve_time_from_time_value_pair)
                return sensor_data
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for a piece of metaadata. When dealing with a list, will append values."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_metadata.__name__ + ": Unexpected empty object: activity_id")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_activity_metadata.__name__ + ": Unexpected empty object: date_time")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_activity_metadata.__name__ + ": Unexpected empty object: key")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_activity_metadata.__name__ + ": Unexpected empty object: value")
            return False
        if create_list is None:
            self.log_error(MongoDatabase.create_activity_metadata.__name__ + ": Unexpected empty object: create_list")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_metadata_list(self, activity_id, key, values):
        """Create method for a list of metaadata values. Will overwrite existing data."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_metadata_list.__name__ + ": Unexpected empty object: activity_id")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_activity_metadata_list.__name__ + ": Unexpected empty object: key")
            return False
        if values is None:
            self.log_error(MongoDatabase.create_activity_metadata_list.__name__ + ": Unexpected empty object: values")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None:
                value_list = []

                for value in values:
                    time_value_pair = {str(value[0]): float(value[1])}
                    value_list.append(time_value_pair)

                value_list.sort(key=retrieve_time_from_time_value_pair)
                activity[key] = value_list
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_sets_and_reps_data(self, activity_id, sets):
        """Create method for a list of of metaadata values."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_sets_and_reps_data.__name__ + ": Unexpected empty object: activity_id")
            return False
        if sets is None:
            self.log_error(MongoDatabase.create_activity_sets_and_reps_data.__name__ + ": Unexpected empty object: sets")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None:
                activity[Keys.APP_SETS_KEY] = sets
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_accelerometer_reading(self, device_str, activity_id, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if device_str is None:
            self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not accels:
            self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Unexpected empty object: accels")
            return False

        try:
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was not found then create it.
            if activity is None:
                first_accel = accels[0]
                if self.create_activity(activity_id, "", first_accel[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str})

            # If the activity was found.
            if activity is not None:
                accel_list = []
                if Keys.APP_ACCELEROMETER_KEY in activity:
                    accel_list = activity[Keys.APP_ACCELEROMETER_KEY]
                for accel in accels:
                    # Make sure time values are monotonically increasing.
                    if accel_list and int(accel_list[-1][Keys.ACCELEROMETER_TIME_KEY]) > accel[0]:
                        self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Received out-of-order time value.")
                    else:
                        value = {Keys.ACCELEROMETER_TIME_KEY: accel[0], Keys.ACCELEROMETER_AXIS_NAME_X: accel[1], Keys.ACCELEROMETER_AXIS_NAME_Y: accel[2], Keys.ACCELEROMETER_AXIS_NAME_Z: accel[3]}
                        accel_list.append(value)

                activity[Keys.APP_ACCELEROMETER_KEY] = accel_list
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_summary(self, activity_id, summary_data):
        """Create method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return False
        if summary_data is None:
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Unexpected empty object: summary_data")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None:
                activity[Keys.ACTIVITY_SUMMARY_KEY] = summary_data
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_summary(self, activity_id):
        """Returns the activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None and Keys.ACTIVITY_SUMMARY_KEY in activity:
                return activity[Keys.ACTIVITY_SUMMARY_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def delete_activity_summary(self, activity_id):
        """Delete method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.delete_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None:
                pass
        except:
            self.log_error(traceback.format_exc())
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
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None:
                data = []
                if Keys.ACTIVITY_TAGS_KEY in activity:
                    data = activity[Keys.ACTIVITY_TAGS_KEY]
                data.append(tag)
                activity[Keys.ACTIVITY_TAGS_KEY] = data
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_tags_on_activity(self, activity, tags):
        """Adds a tag to the specified activity."""
        if activity is None:
            self.log_error(MongoDatabase.create_tags_on_activity.__name__ + ": Unexpected empty object: activity")
            return False
        if tags is None:
            self.log_error(MongoDatabase.create_tags_on_activity.__name__ + ": Unexpected empty object: tags")
            return False

        try:
            activity[Keys.ACTIVITY_TAGS_KEY] = tags
            self.activities_collection.save(activity)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_tags(self, activity_id):
        """Retrieves all the tags for the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_tags.__name__ + ": Unexpected empty object: activity_id")
            return []

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found and contains tags.
            if activity is not None and Keys.ACTIVITY_TAGS_KEY in activity:
                return activity[Keys.ACTIVITY_TAGS_KEY]
        except:
            self.log_error(traceback.format_exc())
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
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
            if activity is not None and Keys.ACTIVITY_TAGS_KEY in activity:
                data = activity[Keys.ACTIVITY_TAGS_KEY]
                data.remove(tag)
                activity[Keys.ACTIVITY_TAGS_KEY] = data
                self.activities_collection.save(activity)
                return True
        except:
            self.log_error(traceback.format_exc())
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
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found.
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
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_comments(self, activity_id):
        """Returns a list containing all of the comments on the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_comments.__name__ + ": Unexpected empty object: activity_id")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({Keys.ACTIVITY_ID_KEY: activity_id})

            # If the activity was found and contains comments.
            if activity is not None and Keys.ACTIVITY_COMMENTS_KEY in activity:
                return activity[Keys.ACTIVITY_COMMENTS_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_workout(self, user_id, workout_obj):
        """Create method for a workout."""
        if user_id is None:
            self.log_error(MongoDatabase.create_workout.__name__ + ": Unexpected empty object: user_id")
            return False
        if workout_obj is None:
            self.log_error(MongoDatabase.create_workout.__name__ + ": Unexpected empty object: workout_obj")
            return False

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was not found then create it.
            if workouts_doc is None:
                post = {}
                post[Keys.WORKOUT_PLAN_USER_ID_KEY] = user_id
                post[Keys.WORKOUT_PLAN_CALENDAR_ID_KEY] = str(uuid.uuid4()) # Create a calendar ID
                post[Keys.WORKOUT_LIST_KEY] = []
                self.workouts_collection.insert(post)
                workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was found (or created).
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:

                # Make sure we have a calendar ID.
                if Keys.WORKOUT_PLAN_CALENDAR_ID_KEY not in workouts_doc:
                    workouts_doc[Keys.WORKOUT_PLAN_CALENDAR_ID_KEY] = str(uuid.uuid4()) # Create a calendar ID

                # Make sure this workout isn't already in the list.
                last_scheduled_workout = 0
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]
                for workout in workouts_list:
                    if Keys.WORKOUT_ID_KEY in workout and workout[Keys.WORKOUT_ID_KEY] == workout_obj.workout_id:
                        return False
                    if Keys.WORKOUT_SCHEDULED_TIME_KEY in workout and workout[Keys.WORKOUT_SCHEDULED_TIME_KEY] > last_scheduled_workout:
                        last_scheduled_workout = workout[Keys.WORKOUT_SCHEDULED_TIME_KEY]

                # Add the workout to the list.
                workout = workout_obj.to_dict()
                workouts_list.append(workout)

                # Update and save the document.
                workouts_doc[Keys.WORKOUT_LIST_KEY] = workouts_list
                workouts_doc[Keys.WORKOUT_LAST_SCHEDULED_WORKOUT_TIME_KEY] = last_scheduled_workout
                self.workouts_collection.save(workouts_doc)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_workout(self, user_id, workout_id):
        """Retrieve method for the workout with the specified user and ID."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_workout.__name__ + ": Unexpected empty object: user_id")
            return None
        if workout_id is None:
            self.log_error(MongoDatabase.retrieve_workout.__name__ + ": Unexpected empty object: workout_id")
            return None

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]

                # Find the workout in the list.
                for workout in workouts_list:
                    if Keys.WORKOUT_ID_KEY in workout and str(workout[Keys.WORKOUT_ID_KEY]) == workout_id:
                        workout_obj = Workout.Workout(user_id)
                        workout_obj.from_dict(workout)
                        return workout_obj
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_workouts_for_user(self, user_id):
        """Retrieve method for the ical calendar ID for with specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_workouts_for_user.__name__ + ": Unexpected empty object: user_id")
            return None

        workouts = []

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]

                # Create an object for each workout in the list.
                for workout in workouts_list:
                    workout_obj = Workout.Workout(user_id)
                    workout_obj.from_dict(workout)
                    workouts.append(workout_obj)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return workouts

    def retrieve_workouts_calendar_id_for_user(self, user_id):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_workouts_calendar_id_for_user.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was found and it has a calendar ID.
            if workouts_doc is not None and Keys.WORKOUT_PLAN_CALENDAR_ID_KEY in workouts_doc:
                return workouts_doc[Keys.WORKOUT_PLAN_CALENDAR_ID_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_workouts_by_calendar_id(self, calendar_id):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if calendar_id is None:
            self.log_error(MongoDatabase.retrieve_workouts_by_calendar_id.__name__ + ": Unexpected empty object: calendar_id")
            return None

        workouts = []

        try:
            # Find the user's document with the specified calendar ID.
            workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_CALENDAR_ID_KEY: calendar_id})

            # If the workouts document was found then return the workouts list.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc and Keys.WORKOUT_PLAN_USER_ID_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]

                # Create an object for each workout in the list.
                for workout in workouts_list:
                    workout_obj = Workout.Workout(workouts_doc[Keys.WORKOUT_PLAN_USER_ID_KEY])
                    workout_obj.from_dict(workout)
                    workouts.append(workout_obj)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return workouts

    def update_workouts_for_user(self, user_id, workout_objs):
        """Update method for a list of workout objects."""
        if user_id is None:
            self.log_error(MongoDatabase.update_workouts_for_user.__name__ + ": Unexpected empty object: user_id")
            return False
        if workout_objs is None:
            self.log_error(MongoDatabase.update_workouts_for_user.__name__ + ": Unexpected empty object: workout_objs")
            return False

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was not found then create it.
            if workouts_doc is None:
                post = {}
                post[Keys.WORKOUT_PLAN_USER_ID_KEY] = user_id
                post[Keys.WORKOUT_LIST_KEY] = []
                self.workouts_collection.insert(post)
                workouts_doc = self.workouts_collection.find_one({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was found (or created).
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:

                # Update and save the document.
                workouts_doc[Keys.WORKOUT_LIST_KEY] = []
                for workout_obj in workout_objs:
                    workouts_doc[Keys.WORKOUT_LIST_KEY].append(workout_obj.to_dict())
                self.workouts_collection.save(workouts_doc)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_workout(self, user_id, workout_id):
        """Delete method for the workout with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_workout.__name__ + ": Unexpected empty object: user_id")
            return None
        if workout_id is None:
            self.log_error(MongoDatabase.delete_workout.__name__ + ": Unexpected empty object: workout_id")
            return False

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find({Keys.WORKOUT_PLAN_USER_ID_KEY: user_id})

            # If the workouts document was found and it contains the specified workout.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]
                
                deleted_result = self.workouts_collection.delete_one({Keys.DATABASE_ID_KEY: workout_id_obj})
                if deleted_result is not None:
                    return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_users_without_scheduled_workouts(self):
        """Returns a list of user IDs for users who have workout plans that need to be re-run."""
        try:
            user_ids = []
            now = time.time()
            workout_docs = self.workouts_collection.find({Keys.WORKOUT_LAST_SCHEDULED_WORKOUT_TIME_KEY: {"$lt": now}})
            for workout_doc in workout_docs:
                if Keys.WORKOUT_LAST_SCHEDULED_WORKOUT_TIME_KEY in workout_doc and workout_doc[Keys.WORKOUT_LAST_SCHEDULED_WORKOUT_TIME_KEY] < now:
                    user_id = workout_doc[Keys.WORKOUT_PLAN_USER_ID_KEY]
                    user_ids.append(user_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return user_ids

    def create_gear(self, user_id, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Create method for gear."""
        if user_id is None:
            self.log_error(MongoDatabase.create_gear.__name__ + ": Unexpected empty object: user_id")
            return False
        if gear_id is None:
            self.log_error(MongoDatabase.create_gear.__name__ + ": Unexpected empty object: gear_id")
            return False
        if gear_type is None:
            self.log_error(MongoDatabase.create_gear.__name__ + ": Unexpected empty object: gear_type")
            return False
        if gear_name is None:
            self.log_error(MongoDatabase.create_gear.__name__ + ": Unexpected empty object: gear_name")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Update the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]
                new_gear = {}
                new_gear[Keys.GEAR_ID_KEY] = str(gear_id)
                new_gear[Keys.GEAR_TYPE_KEY] = gear_type
                new_gear[Keys.GEAR_NAME_KEY] = gear_name
                new_gear[Keys.GEAR_DESCRIPTION_KEY] = gear_description
                new_gear[Keys.GEAR_ADD_TIME_KEY] = int(gear_add_time)
                new_gear[Keys.GEAR_RETIRE_TIME_KEY] = int(gear_retire_time)
                gear_list.append(new_gear)
                user[Keys.GEAR_KEY] = gear_list
                self.users_collection.save(user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_gear(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_gear.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Read the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]
                return gear_list
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_gear(self, user_id, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: user_id")
            return None
        if gear_id is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: gear_id")
            return False
        if gear_type is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: gear_type")
            return False
        if gear_name is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: gear_name")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Update the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]
                    gear_index = 0
                    for gear in gear_list:
                        if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                            gear[Keys.GEAR_TYPE_KEY] = gear_type
                            gear[Keys.GEAR_NAME_KEY] = gear_name
                            gear[Keys.GEAR_DESCRIPTION_KEY] = gear_description
                            gear[Keys.GEAR_ADD_TIME_KEY] = int(gear_add_time)
                            gear[Keys.GEAR_RETIRE_TIME_KEY] = int(gear_retire_time)
                            gear_list.pop(gear_index)
                            gear_list.append(gear)
                            user[Keys.GEAR_KEY] = gear_list
                            self.users_collection.save(user)
                            return True
                        gear_index = gear_index + 1
        except:
            self.log_error(traceback.format_exc())
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
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Update the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]
                    gear_index = 0
                    for gear in gear_list:
                        if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                            gear_list.pop(gear_index)
                            user[Keys.GEAR_KEY] = gear_list
                            self.users_collection.save(user)
                            return True
                        gear_index = gear_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_all_gear(self, user_id):
        """Delete method for the gear with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_gear.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Update the gear list.
                if Keys.GEAR_KEY in user:
                    user[Keys.GEAR_KEY] = []
                    self.users_collection.save(user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
        
    def create_service_record(self, user_id, gear_id, service_record_id, record_date, record_description):
        """Create method for gear service records."""
        if user_id is None:
            self.log_error(MongoDatabase.create_service_record.__name__ + ": Unexpected empty object: user_id")
            return None
        if gear_id is None:
            self.log_error(MongoDatabase.create_service_record.__name__ + ": Unexpected empty object: gear_id")
            return False
        if service_record_id is None:
            self.log_error(MongoDatabase.create_service_record.__name__ + ": Unexpected empty object: service_record_id")
            return False
        if record_date is None:
            self.log_error(MongoDatabase.create_service_record.__name__ + ": Unexpected empty object: record_date")
            return False
        if record_description is None:
            self.log_error(MongoDatabase.create_service_record.__name__ + ": Unexpected empty object: record_description")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Find the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]

                    # Find the gear.
                    for gear in gear_list:
                        if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                            service_rec = {}
                            service_rec[Keys.SERVICE_RECORD_ID_KEY] = str(service_record_id)
                            service_rec[Keys.SERVICE_RECORD_DATE_KEY] = int(record_date)
                            service_rec[Keys.SERVICE_RECORD_DESCRIPTION_KEY] = record_description

                            service_history = []
                            if Keys.GEAR_SERVICE_HISTORY in gear:
                                service_history = gear[Keys.GEAR_SERVICE_HISTORY]
                            service_history.append(service_rec)
                            gear[Keys.GEAR_SERVICE_HISTORY] = service_history

                            self.users_collection.save(user)
                            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_service_record(self, user_id, gear_id, service_record_id):
        """Delete method for the service record with the specified user and gear ID."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_service_record.__name__ + ": Unexpected empty object: user_id")
            return None
        if gear_id is None:
            self.log_error(MongoDatabase.delete_service_record.__name__ + ": Unexpected empty object: gear_id")
            return False
        if service_record_id is None:
            self.log_error(MongoDatabase.delete_service_record.__name__ + ": Unexpected empty object: service_record_id")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({Keys.DATABASE_ID_KEY: user_id_obj})

            # If the user's document was found.
            if user is not None:

                # Find the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]

                    # Find the gear.
                    for gear in gear_list:
                        if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                            if Keys.GEAR_SERVICE_HISTORY in gear:
                                service_history = gear[Keys.GEAR_SERVICE_HISTORY]
                                record_index = 0
                                for service_record in service_history:
                                    if Keys.SERVICE_RECORD_ID_KEY in service_record and service_record[Keys.SERVICE_RECORD_ID_KEY] == service_record_id:
                                        service_history.pop(record_index)
                                        gear[Keys.GEAR_SERVICE_HISTORY] = service_history

                                        self.users_collection.save(user)
                                        return True
                                    record_index = record_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_deferred_task(self, user_id, task_type, task_id, details, status):
        """Create method for tracking a deferred task, such as a file import or activity analysis."""
        if user_id is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: user_id")
            return None
        if task_type is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: task_type")
            return False
        if task_id is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: task_id")
            return False
        if status is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: status")
            return False

        try:
            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({Keys.DEFERRED_TASKS_USER_ID: user_id})

            # If the user's tasks document was not found then create it.
            if user_tasks is None:
                post = {Keys.DEFERRED_TASKS_USER_ID: user_id}
                self.tasks_collection.insert(post)
                user_tasks = self.tasks_collection.find_one({Keys.DEFERRED_TASKS_USER_ID: user_id})

            # If the user's tasks document was found.
            if user_tasks is not None:

                # Get the list of existing tasks.
                deferred_tasks = []
                if Keys.TASKS_KEY in user_tasks:
                    deferred_tasks = user_tasks[Keys.TASKS_KEY]

                # Create an entry for the new task.
                task = {}
                task[Keys.TASK_ID_KEY] = task_id
                task[Keys.TASK_TYPE_KEY] = task_type
                task[Keys.TASK_DETAILS_KEY] = details
                task[Keys.TASK_STATUS_KEY] = status

                # Append it to the list.
                deferred_tasks.append(task)
                user_tasks[Keys.TASKS_KEY] = deferred_tasks

                # Update the database.
                self.tasks_collection.save(user_tasks)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_deferred_tasks(self, user_id):
        """Retrieve method for returning all the deferred tasks for a given user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_deferred_tasks.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({Keys.DEFERRED_TASKS_USER_ID: user_id})

            # If the user's tasks document was found.
            if user_tasks is not None and Keys.TASKS_KEY in user_tasks:
                return user_tasks[Keys.TASKS_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_deferred_task(self, user_id, task_id, status):
        """Updated method for deferred task status."""
        if user_id is None:
            self.log_error(MongoDatabase.update_deferred_task.__name__ + ": Unexpected empty object: user_id")
            return None
        if task_id is None:
            self.log_error(MongoDatabase.update_deferred_task.__name__ + ": Unexpected empty object: task_id")
            return False
        if status is None:
            self.log_error(MongoDatabase.update_deferred_task.__name__ + ": Unexpected empty object: status")
            return False

        try:
            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({Keys.DEFERRED_TASKS_USER_ID: user_id})

            # If the user's tasks document was found.
            if user_tasks is not None and Keys.TASKS_KEY in user_tasks:

                # Find and update the record.
                for task in user_tasks:
                    if Keys.TASK_ID_KEY in task and task[Keys.TASK_ID_KEY] == task_id:
                        task[Keys.TASK_STATUS_KEY] = status

                # Update the database.
                self.tasks_collection.save(user_tasks)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
