# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2017 Michael J Simms
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
import DatabaseException
import InputChecker
import Keys
import Perf
import Workout

def insert_into_collection(collection, doc):
    """Handles differences in document insertion between pymongo 3 and 4."""
    if int(pymongo.__version__[0]) < 4:
        result = collection.insert(doc)
    else:
        result = collection.insert_one(doc)
    return result is not None and result.inserted_id is not None 

def update_collection(collection, doc):
    """Handles differences in document updates between pymongo 3 and 4."""
    if int(pymongo.__version__[0]) < 4:
        collection.save(doc)
        return True
    else:
        query = { Keys.DATABASE_ID_KEY: doc[Keys.DATABASE_ID_KEY] }
        new_values = { "$set" : doc }
        result = collection.update_one(query, new_values)
        return result.matched_count > 0 

def update_activities_collection(self, activity):
    """Handles differences in document updates between pymongo 3 and 4 with activities collection-specific logic."""
    activity[Keys.ACTIVITY_LAST_UPDATED_KEY] = time.time()
    return update_collection(self.activities_collection, activity)

def retrieve_time_from_location(location):
    """Used with the sort function."""
    return location['time']

def retrieve_time_from_time_value_pair(value):
    """Used with the sort function."""
    return list(value.keys())[0]


class Device(object):
    def __init__(self):
        self.id = 0
        self.name = ""
        self.description = ""
        super(Device, self).__init__()


class MongoDatabase(Database.Database):
    """Mongo DB implementation of the application database."""
    conn = None
    database = None
    users_collection = None
    activities_collection = None
    workouts_collection = None
    tasks_collectoin = None
    uploads_collection = None
    sessions_collection = None

    def __init__(self):
        Database.Database.__init__(self)

    def connect(self, config):
        """Connects/creates the database"""
        try:
            # If we weren't given a database URL then assume localhost and default port.
            database_url = config.get_database_url()
            self.conn = pymongo.MongoClient('mongodb://' + database_url + '/?uuidRepresentation=pythonLegacy')

            # Database.
            self.database = self.conn['openworkoutdb']
            if self.database is None:
                raise DatabaseException.DatabaseException("Could not connect to MongoDB.")

            # Handles to the various collections.
            self.users_collection = self.database['users']
            self.activities_collection = self.database['activities']
            self.records_collection = self.database['records']
            self.workouts_collection = self.database['workouts']
            self.tasks_collection = self.database['tasks']
            self.uploads_collection = self.database['uploads']
            self.sessions_collection = self.database['sessions']

            # Create indexes.
            self.activities_collection.create_index(Keys.ACTIVITY_ID_KEY)
        except pymongo.errors.ConnectionFailure as e:
            raise DatabaseException.DatabaseException("Could not connect to MongoDB: %s" % e)

    def total_users_count(self):
        """Returns the number of users in the database."""
        try:
            if int(pymongo.__version__[0]) < 4:
                return self.users_collection.count()
            return self.users_collection.count_documents({})
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return 0

    def total_activities_count(self):
        """Returns the number of activities in the database."""
        try:
            if int(pymongo.__version__[0]) < 4:
                return self.activities_collection.count()
            return self.activities_collection.count_documents({})
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return 0

    def list_excluded_activity_keys(self):
        """This is the list of stuff we don't need to return when we're summarizing activities."""
        exclude_keys = {}
        exclude_keys[Keys.APP_LOCATIONS_KEY] = False
        exclude_keys[Keys.APP_ACCELEROMETER_KEY] = False
        exclude_keys[Keys.APP_CURRENT_SPEED_KEY] = False
        exclude_keys[Keys.APP_HEART_RATE_KEY] = False
        exclude_keys[Keys.APP_CADENCE_KEY] = False
        exclude_keys[Keys.APP_POWER_KEY] = False
        return exclude_keys

    #
    # User management methods
    #

    def create_user(self, username, realname, passhash):
        """Create method for a user."""
        if username is None:
            raise Exception("Unexpected empty object: username")
        if realname is None:
            raise Exception("Unexpected empty object: realname")
        if passhash is None:
            raise Exception("Unexpected empty object: passhash")
        if len(username) == 0:
            raise Exception("username too short")
        if len(realname) == 0:
            raise Exception("realname too short")
        if len(passhash) == 0:
            raise Exception("hash too short")

        try:
            post = { Keys.USERNAME_KEY: username, Keys.REALNAME_KEY: realname, Keys.HASH_KEY: passhash, Keys.DEVICES_KEY: [], Keys.FRIENDS_KEY: [], Keys.DEFAULT_PRIVACY_KEY: Keys.ACTIVITY_VISIBILITY_PUBLIC }
            return insert_into_collection(self.users_collection, post)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user_details(self, username):
        """Retrieve method for a user."""
        if username is None:
            raise Exception("Unexpected empty object: username")
        if len(username) == 0:
            raise Exception("username is empty")

        try:
            return self.users_collection.find_one({ Keys.USERNAME_KEY: username })
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user(self, username):
        """Retrieve method for a user."""
        if username is None:
            raise Exception("Unexpected empty object: username")
        if len(username) == 0:
            raise Exception("username is empty")

        try:
            # Find the user.
            result_keys = { Keys.DATABASE_ID_KEY: 1, Keys.HASH_KEY: 1, Keys.REALNAME_KEY: 1 }
            user = self.users_collection.find_one({ Keys.USERNAME_KEY: username }, result_keys)

            # If the user was found.
            if user is not None:
                return str(user[Keys.DATABASE_ID_KEY]), user[Keys.HASH_KEY], str(user[Keys.REALNAME_KEY])
            return None, None, None
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None, None, None

    def retrieve_user_doc_from_id(self, user_id):
        """Retrieve method for a user."""
        user_id_obj = ObjectId(str(user_id))
        return self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

    def retrieve_user_from_id(self, user_id):
        """Retrieve method for a user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            result_keys = { Keys.USERNAME_KEY: 1, Keys.REALNAME_KEY: 1 }
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj }, result_keys)

            # If the user was found.
            if user is not None:
                return user[Keys.USERNAME_KEY], user[Keys.REALNAME_KEY]
            return None, None
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None, None

    def retrieve_user_from_api_key(self, api_key):
        """Retrieve method for a user."""
        if api_key is None:
            raise Exception("Unexpected empty object: api_key")

        try:
            # Find the user.
            rate = 100
            query = { Keys.API_KEYS: { Keys.API_KEY: str(api_key), Keys.API_KEY_RATE : rate } }
            result_keys = { Keys.DATABASE_ID_KEY: 1, Keys.HASH_KEY: 1, Keys.REALNAME_KEY: 1 }
            user = self.users_collection.find_one(query, result_keys)

            # If the user was found.
            if user is not None:
                return str(user[Keys.DATABASE_ID_KEY]), user[Keys.HASH_KEY], user[Keys.REALNAME_KEY], rate
            return None, None, None, rate
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None, None, None, None

    def update_user_doc(self, doc):
        """Update method for a user."""
        return update_collection(self.users_collection, doc)

    def update_user(self, user_id, username, realname, passhash):
        """Update method for a user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if username is None:
            raise Exception("Unexpected empty object: username")
        if realname is None:
            raise Exception("Unexpected empty object: realname")
        if len(username) == 0:
            raise Exception("username too short")
        if len(realname) == 0:
            raise Exception("realname too short")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)

            # If the user was found.
            if user is not None:
                user[Keys.USERNAME_KEY] = username
                user[Keys.REALNAME_KEY] = realname
                if passhash is not None:
                    user[Keys.HASH_KEY] = passhash
                return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_user(self, user_id):
        """Delete method for a user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            user_id_obj = ObjectId(str(user_id))
            deleted_result = self.users_collection.delete_one({ Keys.DATABASE_ID_KEY: user_id_obj })
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
            raise Exception("Unexpected empty object: username")
        if len(username) == 0:
            raise Exception("username is empty")

        try:
            # Match on usernames.
            matched_usernames = self.users_collection.find({ Keys.USERNAME_KEY: { "$regex": username } })
            if matched_usernames is not None:
                for matched_user in matched_usernames:
                    user_list.append(matched_user[Keys.USERNAME_KEY])

            # Match real names too.
            matched_realnames = self.users_collection.find({ Keys.REALNAME_KEY: { "$regex": username } })
            if matched_realnames is not None:
                for matched_user in matched_realnames:
                    username = matched_user[Keys.USERNAME_KEY]
                    if username not in user_list:
                        user_list.append(username)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return user_list

    def retrieve_random_user(self):
        """Returns a random user id and name from the database."""
        random_user = self.users_collection.aggregate([{ "$sample": { "size": 1 } }])
        for user in random_user:
            return str(user[Keys.DATABASE_ID_KEY]), user[Keys.USERNAME_KEY]
        return None, None

    #
    # Device management methods
    #

    def create_user_device(self, user_id, device_str):
        """Create method for a device."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Read the devices list.
            devices = []
            if Keys.DEVICES_KEY in user:
                devices = user[Keys.DEVICES_KEY]

            # Append the device to the devices list, if it is not already there.
            if device_str not in devices:
                devices.append(device_str)
                user[Keys.DEVICES_KEY] = devices
                return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return True

    def retrieve_user_devices(self, user_id):
        """Retrieve method for a device."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            result_keys = { Keys.DEVICES_KEY: 1 }
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj }, result_keys)

            # Read the devices list.
            if user is not None and Keys.DEVICES_KEY in user:
                return user[Keys.DEVICES_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def retrieve_user_from_device(self, device_str):
        """Finds the user associated with the device."""
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")
        if len(device_str) == 0:
            raise Exception("Device string not provided")

        try:
            return self.users_collection.find_one({ Keys.DEVICES_KEY: device_str })
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def delete_user_device(self, device_str):
        """Deletes method for a device."""
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")
        if len(device_str) == 0:
            raise Exception("Device string not provided")

        try:
            self.activities_collection.remove({ Keys.ACTIVITY_DEVICE_STR_KEY: device_str })
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Friend management methods
    #

    def create_pending_friend_request(self, user_id, target_id):
        """Appends a user to the friends list of the user with the specified id."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if target_id is None:
            raise Exception("Unexpected empty object: target_id")

        try:
            # Find the user whose friendship is being requested.
            user = self.retrieve_user_doc_from_id(target_id)
            if user is None:
                return False

            # If the user was found then add the target user to the pending friends list.
            pending_friends_list = []
            if Keys.FRIEND_REQUESTS_KEY in user:
                pending_friends_list = user[Keys.FRIEND_REQUESTS_KEY]
            if user_id not in pending_friends_list:
                pending_friends_list.append(user_id)
                user[Keys.FRIEND_REQUESTS_KEY] = pending_friends_list
                return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_pending_friends(self, user_id):
        """Returns the user ids for all users that are pending confirmation as friends of the specified user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Only return these keys.
            result_keys = { Keys.USERNAME_KEY: 1, Keys.REALNAME_KEY: 1, Keys.REQUESTING_USER_KEY: 1 }

            # Find the users whose friendship we have requested.
            pending_friends_list = []
            pending_friends = self.users_collection.find({ Keys.FRIEND_REQUESTS_KEY: user_id }, result_keys)
            for pending_friend in pending_friends:
                pending_friend[Keys.DATABASE_ID_KEY] = str(pending_friend[Keys.DATABASE_ID_KEY])
                pending_friend[Keys.REQUESTING_USER_KEY] = "self"
                pending_friends_list.append(pending_friend)

            # Find the users who have requested our friendship.
            user = self.retrieve_user_doc_from_id(user_id)

            # If we found ourselves.
            if user is not None:
                temp_friend_id_list = []
                if Keys.FRIEND_REQUESTS_KEY in user:
                    temp_friend_id_list = user[Keys.FRIEND_REQUESTS_KEY]
                for temp_friend_id in temp_friend_id_list:
                    temp_friend_id_obj = ObjectId(str(temp_friend_id))
                    pending_friend = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: temp_friend_id_obj }, result_keys)
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
            raise Exception("Unexpected empty object: user_id")
        if target_id is None:
            raise Exception("Unexpected empty object: target_id")

        try:
            # Find the user whose friendship is being requested.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # If the user was found then add the target user to the pending friends list.
            pending_friends_list = []
            if Keys.FRIEND_REQUESTS_KEY in user:
                pending_friends_list = user[Keys.FRIEND_REQUESTS_KEY]
            if target_id in pending_friends_list:
                pending_friends_list.remove(target_id)
                user[Keys.FRIEND_REQUESTS_KEY] = pending_friends_list
                return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_friend(self, user_id, target_id):
        """Appends a user to the friends list of the user with the specified id."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if target_id is None:
            raise Exception("Unexpected empty object: target_id")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)

            # Find the target user.
            target_user = self.retrieve_user_doc_from_id(target_id)

            # If the users were found then add each other to their friends lists.
            if user is not None and target_user is not None:

                # Update the user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in user:
                    friends_list = user[Keys.FRIENDS_KEY]
                if target_id not in friends_list:
                    friends_list.append(target_id)
                    user[Keys.FRIENDS_KEY] = friends_list
                    self.update_user_doc(user)

                # Update the target user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in target_user:
                    friends_list = target_user[Keys.FRIENDS_KEY]
                if user_id not in friends_list:
                    friends_list.append(user_id)
                    target_user[Keys.FRIENDS_KEY] = friends_list
                    self.update_user_doc(target_user)

                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_friends(self, user_id):
        """Returns the user ids for all users that are friends with the user who has the specified id."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Only return these keys.
            result_keys = { Keys.USERNAME_KEY: 1, Keys.REALNAME_KEY: 1 }

            # Find the user's friends list.
            friends_list = []
            friends = self.users_collection.find({ Keys.FRIENDS_KEY: user_id }, result_keys)
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
            raise Exception("Unexpected empty object: user_id")
        if target_id is None:
            raise Exception("Unexpected empty object: target_id")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)

            # Find the target user.
            target_user = self.retrieve_user_doc_from_id(target_id)

            # If the users were found then add each other to their friends lists.
            if user is not None and target_user is not None:

                # Update the user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in user:
                    friends_list = user[Keys.FRIENDS_KEY]
                if target_id in friends_list:
                    friends_list.remove(target_id)
                    user[Keys.FRIENDS_KEY] = friends_list
                    self.update_user_doc(user)

                # Update the target user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in target_user:
                    friends_list = target_user[Keys.FRIENDS_KEY]
                if user_id in friends_list:
                    friends_list.remove(user_id)
                    target_user[Keys.FRIENDS_KEY] = friends_list
                    self.update_user_doc(target_user)

                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # User settings methods
    #

    def update_user_setting(self, user_id, key, value, update_time):
        """Create/update method for user preferences."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if key is None:
            raise Exception("Unexpected empty object: key")
        if value is None:
            raise Exception("Unexpected empty object: value")
        if update_time is None:
            raise Exception("Unexpected empty object: update_time")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Do not replace a newer value with an older value.
            if Keys.USER_SETTINGS_LAST_UPDATED_KEY not in user:
                user[Keys.USER_SETTINGS_LAST_UPDATED_KEY] = {}
            elif key in user[Keys.USER_SETTINGS_LAST_UPDATED_KEY] and user[Keys.USER_SETTINGS_LAST_UPDATED_KEY][key] > update_time:
                return False

            # Update.
            user[Keys.USER_SETTINGS_LAST_UPDATED_KEY][key] = update_time
            user[key] = value
            return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user_setting(self, user_id, key):
        """Retrieve method for user preferences."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if key is None:
            raise Exception("Unexpected empty object: key")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return None

            # We want to search for keys in a case insensitive manner.
            user_lower = { k.lower():v for k,v in user.items() }
            key_lower = key.lower()
            valid_settings = set(k.lower() for k in Keys.USER_SETTINGS)

            # Find the setting.
            if user_lower is not None and key_lower in user_lower and key_lower in valid_settings:
                return user_lower[key_lower]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user_settings(self, user_id, keys):
        """Retrieve method for user preferences."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if keys is None:
            raise Exception("Unexpected empty object: keys")

        try:
            # Find the user.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return []

            # We want to search for keys in a case insensitive manner.
            user_lower = { k.lower():v for k,v in user.items() }
            keys_lower = set(k.lower() for k in keys)
            valid_settings = set(k.lower() for k in Keys.USER_SETTINGS)

            # Find the settings.
            results = []
            for key in keys_lower:
                if key in user_lower and key in valid_settings:
                    results.append({key: user_lower[key]})
            return results
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    #
    # Personal record management methods
    #

    def create_user_personal_records(self, user_id, records):
        """Create method for a user's personal record."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if records is None:
            raise Exception("Unexpected empty object: records")

        try:
            # Find the user's records collection.
            user_id_str = str(user_id)
            user_records = self.records_collection.find_one({ Keys.USER_ID_KEY: user_id_str })

            # If the collection was found.
            if user_records is None:
                post = { Keys.USER_ID_KEY: user_id_str, Keys.PERSONAL_RECORDS_KEY: records }
                return insert_into_collection(self.records_collection, post)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def update_user_personal_records(self, user_id, records):
        """Create method for a user's personal record. These are the bests across all activities. Activity records are the bests for individual activities."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if records is None or len(records) == 0:
            raise Exception("Unexpected empty object: records")

        try:
            # Find the user's records collection.
            user_id_str = str(user_id)
            user_records = self.records_collection.find_one({ Keys.USER_ID_KEY: user_id_str })

            # If the collection was found.
            if user_records is not None:
                user_records[Keys.PERSONAL_RECORDS_KEY] = records
                return update_collection(self.records_collection, user_records)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_all_user_personal_records(self, user_id):
        """Delete method for a user's personal record. Deletes the entire personal record cache."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Delete the user's records collection.
            user_id_str = str(user_id)
            deleted_result = self.records_collection.delete_one({ Keys.USER_ID_KEY: user_id_str })
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Activity bests management methods
    #

    def create_activity_bests(self, user_id, activity_id, activity_type, activity_time, bests):
        """Create method for a user's personal records for a given activity."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if activity_type is None:
            raise Exception("Unexpected empty object: activity_type")
        if activity_time is None:
            raise Exception("Unexpected empty object: activity_time")
        if bests is None:
            raise Exception("Unexpected empty object: bests")

        try:
            # Find the user's records collection.
            user_records = self.records_collection.find_one({ Keys.USER_ID_KEY: user_id })
            if user_records is not None:
                bests[Keys.ACTIVITY_TYPE_KEY] = activity_type
                bests[Keys.ACTIVITY_START_TIME_KEY] = activity_time
                user_records[activity_id] = bests
                return update_collection(self.records_collection, user_records)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_bests_for_user(self, user_id):
        """Retrieve method for a user's activity records."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            user_records = self.records_collection.find_one({ Keys.USER_ID_KEY: user_id })
            if user_records is None:
                return {}

            # Each record is named using the activity ID of the corresponding activity.
            bests = {}
            for activity_id in user_records:
                if InputChecker.is_uuid(activity_id):
                    activity_bests = user_records[activity_id]
                    bests[activity_id] = activity_bests
            return bests
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return {}

    def retrieve_bounded_activity_bests_for_user(self, user_id, cutoff_time_lower, cutoff_time_higher):
        """Retrieve method for a user's activity records. Only activities more recent than the specified cutoff time will be returned."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if cutoff_time_lower is None:
            raise Exception("Unexpected empty object: cutoff_time_lower")
        if cutoff_time_higher is None:
            raise Exception("Unexpected empty object: cutoff_time_higher")

        try:
            user_records = self.records_collection.find_one({ Keys.USER_ID_KEY: user_id })
            if user_records is None:
                return {}

            # Each record is named using the activity ID of the corresponding activity.
            bests = {}
            for activity_id in user_records:
                if InputChecker.is_uuid(activity_id):
                    activity_bests = user_records[activity_id]
                    if Keys.ACTIVITY_START_TIME_KEY in activity_bests:
                        activity_time = activity_bests[Keys.ACTIVITY_START_TIME_KEY]
                        if activity_time >= cutoff_time_lower and activity_time < cutoff_time_higher:
                            bests[activity_id] = activity_bests
            return bests
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return {}

    def delete_activity_best_for_user(self, user_id, activity_id):
        """Delete method for a user's personal records for a given activity."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            user_records = self.records_collection.find_one({ Keys.USER_ID_KEY: user_id })
            if user_records is not None:
                user_records[activity_id] = {}
                return update_collection(self.records_collection, user_records)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Activity management methods
    #

    @Perf.statistics
    def retrieve_user_activity_list(self, user_id, start_time, end_time, return_all_data):
        """Retrieves the list of activities associated with the specified user."""
        """If return_all_data is False then only metadata is returned."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys()

            if start_time is None or end_time is None:
                return list(self.activities_collection.find({ "$and": [ { Keys.ACTIVITY_USER_ID_KEY: { '$eq': user_id } } ]}, exclude_keys))
            return list(self.activities_collection.find({ "$and": [ { Keys.ACTIVITY_USER_ID_KEY: { '$eq': user_id }}, { Keys.ACTIVITY_START_TIME_KEY: { '$gt': start_time } }, { Keys.ACTIVITY_START_TIME_KEY: { '$lt': end_time } } ]}, exclude_keys))
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    @Perf.statistics
    def retrieve_each_user_activity(self, user_id, context, callback_func, start_time, end_time, return_all_data):
        """Retrieves each user activity and calls the callback function for each one."""
        """Returns TRUE on success, FALSE if an error was encountered."""
        """If return_all_data is False then only metadata is returned."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if callback_func is None:
            raise Exception("Unexpected empty object: callback_func")

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys()

            # Get an iterator to the activities.
            if start_time is None or end_time is None:
                activities_cursor = self.activities_collection.find({ Keys.ACTIVITY_USER_ID_KEY: user_id }, exclude_keys)
            activities_cursor = self.activities_collection.find({ "$and": [ { Keys.ACTIVITY_START_TIME_KEY: { '$gt': start_time } }, { Keys.ACTIVITY_START_TIME_KEY: { '$lt': end_time } } ]}, exclude_keys)

            # Iterate over the results, triggering the callback for each.
            if activities_cursor is not None:
                try:
                    while activities_cursor.alive:
                        activity = activities_cursor.next()
                        callback_func(context, activity, user_id)
                except StopIteration:
                    pass
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    @Perf.statistics
    def retrieve_devices_activity_list(self, devices, start_time, end_time, return_all_data):
        """Retrieves the list of activities associated with the specified devices."""
        if devices is None:
            raise Exception("Unexpected empty object: devices")

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys()

            # Build part of the exptression while sanity checking the input.
            device_list = []
            for device_str in devices:
                if InputChecker.is_uuid(device_str):
                    device_list.append( { Keys.ACTIVITY_DEVICE_STR_KEY: {'$eq': device_str} } )

            # If the device list is empty then just return as there's nothing to do and we'll just get a db error.
            if not device_list:
                return []

            if start_time is None or end_time is None:
                return list(self.activities_collection.find({ "$or": device_list }, exclude_keys))
            return list(self.activities_collection.find({ "$and": [ { "$or": device_list }, { Keys.ACTIVITY_START_TIME_KEY: { '$gt': start_time } }, { Keys.ACTIVITY_START_TIME_KEY: { '$lt': end_time } } ] }, exclude_keys))
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    @Perf.statistics
    def retrieve_each_device_activity(self, user_id, device_str, context, callback_func, start_time, end_time, return_all_data):
        """Retrieves each device activity and calls the callback function for each one."""
        """If return_all_data is False then only metadata is returned."""
        if user_id is None:
            raise Exception("Unexpected empty object: device_str")
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")
        if callback_func is None:
            raise Exception("Unexpected empty object: device_str")

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys()

            # Get an iterator to the activities.
            if start_time is None or end_time is None:
                activities_cursor = self.activities_collection.find({ Keys.ACTIVITY_DEVICE_STR_KEY: device_str }, exclude_keys)
            activities_cursor = self.activities_collection.find({ "$and": [ { Keys.ACTIVITY_DEVICE_STR_KEY: { '$eq': device_str } }, { Keys.ACTIVITY_START_TIME_KEY: { '$gt': start_time } }, { Keys.ACTIVITY_START_TIME_KEY: { '$lt': end_time } } ]}, exclude_keys)

            # Iterate over the results, triggering the callback for each.
            if activities_cursor is not None:
                try:
                    while activities_cursor.alive:
                        activity = activities_cursor.next()
                        callback_func(context, activity, user_id)
                except StopIteration:
                    pass
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    @Perf.statistics
    def retrieve_most_recent_activity_for_device(self, device_str, return_all_data):
        """Retrieves the ID for the most recent activity to be associated with the specified device."""
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys()

            # Find the activity.
            return self.activities_collection.find_one({ Keys.ACTIVITY_DEVICE_STR_KEY: device_str }, exclude_keys, sort=[( '_id', pymongo.DESCENDING )])
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity(self, activity_id, activity_name, date_time, device_str):
        """Create method for an activity."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if activity_name is None:
            raise Exception("Unexpected empty object: activity_name")
        if date_time is None:
            raise Exception("Unexpected empty object: date_time")
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")

        try:
            # Make sure the activity name is a string.
            activity_name = str(activity_name)

            # Create the activity.
            post = { Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_NAME_KEY: activity_name, Keys.ACTIVITY_START_TIME_KEY: date_time, Keys.ACTIVITY_DEVICE_STR_KEY: device_str, Keys.ACTIVITY_VISIBILITY_KEY: "public", Keys.ACTIVITY_LOCATIONS_KEY: [] }
            return insert_into_collection(self.activities_collection, post)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_complete_activity(self, activity):
        """Create method for an activity."""
        if activity is None:
            raise Exception("Unexpected empty object: activity")

        try:
            return insert_into_collection(self.activities_collection, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def recreate_activity(self, activity):
        """Update method for a complete activity."""
        if activity is None:
            raise Exception("Unexpected empty object: activity")

        try:
            deleted_result = self.activities_collection.delete_one({ Keys.ACTIVITY_ID_KEY: activity[Keys.ACTIVITY_ID_KEY] })
            if deleted_result is not None:
                activity.pop(Keys.DATABASE_ID_KEY)
                return insert_into_collection(self.activities_collection, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    @Perf.statistics
    def retrieve_activity(self, activity_id):
        """Retrieve method for an activity, specified by the activity ID."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            # Find the activity.
            return self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: re.compile(activity_id, re.IGNORECASE) })
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    @Perf.statistics
    def retrieve_activity_small(self, activity_id):
        """Retrieve method for an activity, specified by the activity ID."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            # Things we don't need.
            exclude_keys = self.list_excluded_activity_keys()

            # Find the activity.
            return self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: re.compile(activity_id, re.IGNORECASE) }, exclude_keys)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def update_activity(self, device_str, activity_id, locations, sensor_readings_dict, metadata_list_dict):
        """Updates locations, sensor readings, and metadata associated with a moving activity. Provided as a performance improvement over making several database updates."""
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if not locations:
            raise Exception("Unexpected empty object: locations")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str })

            # If the activity was not found then create it.
            if activity is None:
                first_location = locations[0]
                if self.create_activity(activity_id, "", first_location[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str })

            # If the activity was found.
            if activity is not None:

                # Update the locations. Location data is an array, the order is defined in Api.parse_json_loc_obj.
                if len(locations) > 0:

                    # Find any existing location data.
                    old_locations = []
                    if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                        old_locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]

                    # Append the new locations.
                    for location in locations:
                        value = { Keys.LOCATION_TIME_KEY: location[0], Keys.LOCATION_LAT_KEY: location[1], Keys.LOCATION_LON_KEY: location[2], Keys.LOCATION_ALT_KEY: location[3], Keys.LOCATION_HORIZONTAL_ACCURACY_KEY: location[4], Keys.LOCATION_VERTICAL_ACCURACY_KEY: location[5] }
                        old_locations.append(value)

                    # Make sure everything is in the right order, no guarantee we got the updates in the correct order.
                    old_locations.sort(key=retrieve_time_from_location)

                    # Update the database.
                    activity[Keys.ACTIVITY_LOCATIONS_KEY] = old_locations

                # Update the sensor readings.
                if sensor_readings_dict:
                    for sensor_type in sensor_readings_dict:

                        # Existing sensor values.
                        old_value_list = []
                        if sensor_type in activity:
                            old_value_list = activity[sensor_type]

                        # Append new values.
                        for value in sensor_readings_dict[sensor_type]:
                            time_value_pair = { str(value[0]): float(value[1]) }
                            old_value_list.append(time_value_pair)

                        # Sort and update.
                        old_value_list.sort(key=retrieve_time_from_time_value_pair)
                        activity[sensor_type] = old_value_list

                # Update the metadata readings.
                if metadata_list_dict:
                    for metadata_type in metadata_list_dict:

                        # Existing metadata values.
                        old_value_list = []
                        if metadata_type in activity:
                            old_value_list = activity[metadata_type]

                        # Append new values.
                        for value in metadata_list_dict[metadata_type]:
                            time_value_pair = { str(value[0]): float(value[1]) }
                            old_value_list.append(time_value_pair)

                        # Sort and update.
                        old_value_list.sort(key=retrieve_time_from_time_value_pair)
                        activity[metadata_type] = old_value_list

                # Write out the changes.
                return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity(self, activity_id):
        """Delete method for an activity, specified by the activity ID."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            deleted_result = self.activities_collection.delete_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def activity_exists(self, activity_id):
        """Determines whether or not there is a document corresonding to the activity ID."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            return self.activities_collection.count_documents({ Keys.ACTIVITY_ID_KEY: activity_id }, limit = 1) != 0
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def list_activities_with_last_updated_times_before(self, user_id, last_modified_time):
        """Returns a list of activity IDs with last modified times greater than the date provided."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if last_modified_time is None:
            raise Exception("Unexpected empty object: last_modified_time")

        try:
            results = list(self.activities_collection.find({ Keys.ACTIVITY_LAST_UPDATED_KEY: {'$gt': last_modified_time} }, { Keys.DATABASE_ID_KEY: 0, Keys.ACTIVITY_ID_KEY: 1 }))
            results = [x[Keys.ACTIVITY_ID_KEY] for x in results]
            return results
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def retrieve_unanalyzed_activity_list(self, limit):
        try:
            results = list(self.activities_collection.find({ Keys.ACTIVITY_SUMMARY_KEY: {'$exists': 0} }, { Keys.DATABASE_ID_KEY: 0, Keys.ACTIVITY_ID_KEY: 1 }, limit = limit))
            results = [x[Keys.ACTIVITY_ID_KEY] for x in results]
            return results
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    #
    # Activity data methods
    #

    def create_activity_locations(self, device_str, activity_id, locations):
        """Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if not locations:
            raise Exception("Unexpected empty object: locations")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str })

            # If the activity was not found then create it.
            if activity is None:
                first_location = locations[0]
                if self.create_activity(activity_id, "", first_location[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str })

            # If the activity was found.
            if activity is not None:
                location_list = []

                # Get the existing list.
                if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                    location_list = activity[Keys.ACTIVITY_LOCATIONS_KEY]

                # Append the new locations.
                for location in locations:
                    value = { Keys.LOCATION_TIME_KEY: location[0], Keys.LOCATION_LAT_KEY: location[1], Keys.LOCATION_LON_KEY: location[2], Keys.LOCATION_ALT_KEY: location[3] }
                    location_list.append(value)

                # Make sure everything is in order.
                location_list.sort(key=retrieve_time_from_location)

                # Save the changes.
                activity[Keys.ACTIVITY_LOCATIONS_KEY] = location_list
                return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_locations(self, activity_id):
        """Returns all the locations for the specified activity."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return None

            # If the activity was found and it has location data.
            if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
                locations.sort(key=retrieve_time_from_location)
                return locations
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Create method for a piece of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception(" object: activity_id " + str(activity_id))
        if date_time is None:
            raise Exception("Unexpected empty object: date_time")
        if sensor_type is None:
            raise Exception("Unexpected empty object: sensor_type")
        if value is None:
            raise Exception("Unexpected empty object: value")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            value_list = []

            # Get the existing list.
            if sensor_type in activity:
                value_list = activity[sensor_type]

            time_value_pair = { str(date_time): float(value) }
            value_list.append(time_value_pair)
            value_list.sort(key=retrieve_time_from_time_value_pair)

            # Save the changes.
            activity[sensor_type] = value_list
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_sensor_readings(self, activity_id, sensor_type, values):
        """Create method for several pieces of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if sensor_type is None:
            raise Exception("Unexpected empty object: sensor_type")
        if values is None:
            raise Exception("Unexpected empty object: values")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            value_list = []

            # Get the existing list.
            if sensor_type in activity:
                value_list = activity[sensor_type]

            for value in values:
                time_value_pair = { str(value[0]): float(value[1]) }
                value_list.append(time_value_pair)

            value_list.sort(key=retrieve_time_from_time_value_pair)

            # Save the changes.
            activity[sensor_type] = value_list
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity_sensor_readings(self, sensor_type, activity_id):
        """Create method for several pieces of sensor data, such as a heart rate or power meter reading."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if sensor_type is None:
            raise Exception("Unexpected empty object: sensor_type")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            # Save the changes.
            activity[sensor_type] = []
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_event(self, activity_id, event):
        """Inherited from ActivityWriter. 'events' is an array of dictionaries in which each dictionary describes an event."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if event is None:
            raise Exception("Unexpected empty object: event")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            events_list = []

            # Get the existing list.
            if Keys.APP_EVENTS_KEY in activity:
                events_list = activity[Keys.APP_EVENTS_KEY]

            # Update the list.
            events_list.append(event)

            # Save the changes.
            activity[Keys.APP_EVENTS_KEY] = events_list
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_events(self, activity_id, events):
        """Inherited from ActivityWriter. 'events' is an array of dictionaries in which each dictionary describes an event."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if events is None:
            raise Exception("Unexpected empty object: events")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            # Get the existing list.
            events_list = []
            if Keys.APP_EVENTS_KEY in activity:
                events_list = activity[Keys.APP_EVENTS_KEY]

            # Update the list.
            events_list.extend(events)

            # Save the changes.
            activity[Keys.APP_EVENTS_KEY] = events_list
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_or_update_activity_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for a piece of metaadata. When dealing with a list, will append values."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if date_time is None and create_list:
            raise Exception("Unexpected empty object: date_time")
        if key is None:
            raise Exception("Unexpected empty object: key")
        if value is None:
            raise Exception("Unexpected empty object: value")
        if create_list is None:
            raise Exception("Unexpected empty object: create_list")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            # Make sure we're working with a number, if the value is supposed to be a number.
            try:
                if not key in [ Keys.ACTIVITY_NAME_KEY, Keys.ACTIVITY_TYPE_KEY, Keys.ACTIVITY_DESCRIPTION_KEY ]:
                    value = float(value)
            except ValueError:
                pass

            # The metadata is a list.
            if create_list is True:
                value_list = []
                if key in activity:
                    value_list = activity[key]

                time_value_pair = { str(date_time): value }
                value_list.append(time_value_pair)
                value_list.sort(key=retrieve_time_from_time_value_pair)
                activity[key] = value_list
                return update_activities_collection(self, activity)

            # The metadata is a scalar, just make sure to only update it if it has actually changed or was previously non-existent.
            elif key not in activity or activity[key] != value:
                activity[key] = value
                return update_activities_collection(self, activity)

            # It's ok if the value isn't being updated.
            elif activity[key] == value:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_or_update_activity_metadata_list(self, activity_id, key, values):
        """Create method for a list of metaadata values. Will overwrite existing data."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if key is None:
            raise Exception("Unexpected empty object: key")
        if values is None:
            raise Exception("Unexpected empty object: values")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            value_list = []
            if key in activity:
                value_list = activity[key]
            for value in values:
                time_value_pair = { str(value[0]): float(value[1]) }
                value_list.append(time_value_pair)

            value_list.sort(key=retrieve_time_from_time_value_pair)
            activity[key] = value_list
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_lap(self, activity_id, start_time_ms):
        """Create method for a list of of metaadata values."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if start_time_ms is None:
            raise Exception("Unexpected empty object: start_time_ms")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            laps = []
            if Keys.ACTIVITY_LAPS_KEY in activity:
                laps = activity[Keys.ACTIVITY_LAPS_KEY]
            laps.append(start_time_ms)
            activity[Keys.ACTIVITY_LAPS_KEY] = laps
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_sets_and_reps_data(self, activity_id, sets):
        """Create method for a list of of metaadata values."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if sets is None:
            raise Exception("Unexpected empty object: sets")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            activity[Keys.APP_SETS_KEY] = sets
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_accelerometer_reading(self, device_str, activity_id, accels):
        """Adds several accelerometer readings to the database. 'accels' is an array of arrays in the form [time, x, y, z]."""
        if device_str is None:
            raise Exception("Unexpected empty object: device_str")
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if not accels:
            raise Exception("Unexpected empty object: accels")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str })

            # If the activity was not found then create it.
            if activity is None:
                first_accel = accels[0]
                if self.create_activity(activity_id, "", first_accel[0] / 1000, device_str):
                    activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_DEVICE_STR_KEY: device_str })

            # If the activity was found.
            if activity is not None:
                accel_list = []

                # Get the existing list.
                if Keys.APP_ACCELEROMETER_KEY in activity:
                    accel_list = activity[Keys.APP_ACCELEROMETER_KEY]

                for accel in accels:

                    # Make sure time values are monotonically increasing.
                    if accel_list and int(accel_list[-1][Keys.ACCELEROMETER_TIME_KEY]) > accel[0]:
                        self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Received out-of-order time value.")
                    else:
                        value = { Keys.ACCELEROMETER_TIME_KEY: accel[0], Keys.ACCELEROMETER_AXIS_NAME_X: accel[1], Keys.ACCELEROMETER_AXIS_NAME_Y: accel[2], Keys.ACCELEROMETER_AXIS_NAME_Z: accel[3] }
                        accel_list.append(value)

                activity[Keys.APP_ACCELEROMETER_KEY] = accel_list
                return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Activity summary methods
    #

    def create_activity_summary(self, activity_id, summary_data):
        """Create method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if summary_data is None:
            raise Exception("Unexpected empty object: summary_data")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            activity[Keys.ACTIVITY_SUMMARY_KEY] = summary_data
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity_summary(self, activity_id):
        """Delete method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            if Keys.ACTIVITY_SUMMARY_KEY in activity:
                activity[Keys.ACTIVITY_SUMMARY_KEY] = {}
                return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Tag management methods
    #

    def create_tag(self, activity_id, tag):
        """Adds a tag to the specified activity."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if tag is None:
            raise Exception("Unexpected empty object: tag")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            data = []
            if Keys.ACTIVITY_TAGS_KEY in activity:
                data = activity[Keys.ACTIVITY_TAGS_KEY]
            data.append(tag)
            activity[Keys.ACTIVITY_TAGS_KEY] = data
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_tags_on_activity(self, activity, tags):
        """Adds a tag to the specified activity."""
        if activity is None:
            raise Exception("Unexpected empty object: activity")
        if tags is None:
            raise Exception("Unexpected empty object: tags")

        try:
            activity[Keys.ACTIVITY_TAGS_KEY] = tags
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
        
    def create_tags_on_activity_by_id(self, activity_id, tags):
        """Adds a tag to the specified activity."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if tags is None:
            raise Exception("Unexpected empty object: tags")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            activity[Keys.ACTIVITY_TAGS_KEY] = tags
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_tag_from_activity(self, activity, tag):
        """Deletes the specified tag from the activity with the given ID."""
        if activity is None:
            raise Exception("Unexpected empty object: activity")
        if tag is None:
            raise Exception("Unexpected empty object: tag")

        try:
            if Keys.ACTIVITY_TAGS_KEY in activity:
                data = activity[Keys.ACTIVITY_TAGS_KEY]
                data.remove(tag)
                activity[Keys.ACTIVITY_TAGS_KEY] = data
                return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Activity comment management methods
    #

    def create_activity_comment(self, activity_id, commenter_id, comment):
        """Create method for a comment on an activity."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if commenter_id is None:
            raise Exception("Unexpected empty object: commenter_id")
        if comment is None:
            raise Exception("Unexpected empty object: comment")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            data = []
            if Keys.ACTIVITY_COMMENTS_KEY in activity:
                data = activity[Keys.ACTIVITY_COMMENTS_KEY]
            entry_dict = { Keys.ACTIVITY_COMMENTER_ID_KEY: commenter_id, Keys.ACTIVITY_COMMENT_KEY: comment }
            entry_str = json.dumps(entry_dict)
            data.append(entry_str)
            activity[Keys.ACTIVITY_COMMENTS_KEY] = data
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Activity photo management methods
    #

    def create_activity_photo(self, user_id, activity_id, photo_hash):
        """Create method for an activity photo."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if photo_hash is None:
            raise Exception("Unexpected empty object: photo_hash")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })
            if activity is None:
                return False

            # Append the hash of the photo to the photos list.
            photos = []
            if Keys.ACTIVITY_PHOTOS_KEY in activity:
                photos = activity[Keys.ACTIVITY_PHOTOS_KEY]
            photos.append(photo_hash)

            # Remove duplicates.
            photos = list(dict.fromkeys(photos))

            # Save the updated activity.
            activity[Keys.ACTIVITY_PHOTOS_KEY] = photos
            return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity_photo(self, activity_id, photo_id):
        """Deletes the specified tag from the activity with the given ID."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid object: activity_id " + str(activity_id))
        if photo_id is None:
            raise Exception("Unexpected empty object: photo_id")

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None and Keys.ACTIVITY_PHOTOS_KEY in activity:
                photos = activity[Keys.ACTIVITY_PHOTOS_KEY]
                photos.remove(photo_id)
                activity[Keys.ACTIVITY_PHOTOS_KEY] = photos
                return update_activities_collection(self, activity)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Planned workout management methods
    #

    def create_workout(self, user_id, workout_obj):
        """Create method for a workout."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if workout_obj is None:
            raise Exception("Unexpected empty object: workout_obj")

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was not found then create it.
            if workouts_doc is None:
                post = {}
                post[Keys.USER_ID_KEY] = user_id
                post[Keys.WORKOUT_PLAN_CALENDAR_ID_KEY] = str(uuid.uuid4()) # Create a calendar ID
                post[Keys.WORKOUT_LIST_KEY] = []
                insert_into_collection(self.workouts_collection, post)
                workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

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
                return update_collection(self.workouts_collection, workouts_doc)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_planned_workout(self, user_id, workout_id):
        """Retrieve method for the workout with the specified user and ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if workout_id is None:
            raise Exception("Unexpected empty object: workout_id")

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

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

    def retrieve_planned_workouts_for_user(self, user_id, start_time, end_time):
        """Retrieve method for the ical calendar ID for with specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        workouts = []

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]

                # Create an object for each workout in the list.
                for workout in workouts_list:
                    workout_obj = Workout.Workout(user_id)
                    workout_obj.from_dict(workout)
                    scheduled_time = int(time.mktime(workout_obj.scheduled_time.timetuple()))
                    if (start_time is None or start_time == 0 or scheduled_time > start_time) and (end_time is None or end_time == 0 or scheduled_time <= end_time):
                        workouts.append(workout_obj)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return workouts

    def retrieve_planned_workouts_calendar_id_for_user(self, user_id):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was found and it has a calendar ID.
            if workouts_doc is not None and Keys.WORKOUT_PLAN_CALENDAR_ID_KEY in workouts_doc:
                return workouts_doc[Keys.WORKOUT_PLAN_CALENDAR_ID_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_planned_workouts_by_calendar_id(self, calendar_id):
        """Retrieve method for all workouts pertaining to the user with the specified ID."""
        if calendar_id is None:
            raise Exception("Unexpected empty object: calendar_id")

        workouts = []

        try:
            # Find the user's document with the specified calendar ID.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_CALENDAR_ID_KEY: calendar_id })

            # If the workouts document was found then return the workouts list.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc and Keys.USER_ID_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]

                # Create an object for each workout in the list.
                for workout in workouts_list:
                    workout_obj = Workout.Workout(workouts_doc[Keys.USER_ID_KEY])
                    workout_obj.from_dict(workout)
                    workouts.append(workout_obj)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return workouts

    def update_planned_workouts_for_user(self, user_id, workout_objs):
        """Update method for a list of workout objects."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if workout_objs is None:
            raise Exception("Unexpected empty object: workout_objs")

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was not found then create it.
            if workouts_doc is None:
                post = {}
                post[Keys.USER_ID_KEY] = user_id
                post[Keys.WORKOUT_LIST_KEY] = []
                insert_into_collection(self.workouts_collection, post)
                workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:

                # Update and save the document.
                workouts_doc[Keys.WORKOUT_LIST_KEY] = [ workout_obj.to_dict() for workout_obj in workout_objs ]
                return update_collection(self.workouts_collection, workouts_doc)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_planned_workout_for_user(self, user_id, workout_id):
        """Update method for a list of workout objects."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if workout_id is None:
            raise Exception("Unexpected empty object: workout_id")

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:
                workouts_list = workouts_doc[Keys.WORKOUT_LIST_KEY]
                new_list = [i for i in workouts_list if not (i[Keys.WORKOUT_ID_KEY] == workout_id)]
                workouts_doc[Keys.WORKOUT_LIST_KEY] = new_list
                return update_collection(self.workouts_collection, workouts_doc)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_planned_workouts_for_user(self, user_id):
        """Update method for a list of workout objects."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.USER_ID_KEY: user_id })

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:
                workouts_doc[Keys.WORKOUT_LIST_KEY] = []
                return update_collection(self.workouts_collection, workouts_doc)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_users_without_scheduled_workouts(self):
        """Returns a list of user IDs for users who have workout plans that need to be re-run."""
        try:
            user_ids = []
            workout_docs = self.workouts_collection.find({ Keys.WORKOUT_LAST_SCHEDULED_WORKOUT_TIME_KEY: { "$lt": time.time() } })
            for workout_doc in workout_docs:
                if Keys.USER_ID_KEY in workout_doc:
                    user_id = workout_doc[Keys.USER_ID_KEY]
                    user_ids.append(user_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return user_ids

    #
    # Gear default management methods
    #

    def retrieve_gear_defaults(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return []

            # Read the gear list.
            gear_defaults_list = []
            if Keys.GEAR_DEFAULTS_KEY in user:
                gear_defaults_list = user[Keys.GEAR_DEFAULTS_KEY]
            return gear_defaults_list
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_gear_defaults(self, user_id, activity_type, gear_name):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if activity_type is None:
            raise Exception("Unexpected empty object: activity_type")
        if gear_name is None:
            raise Exception("Unexpected empty object: gear_name")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Update the gear list.
            gear_defaults_list = []

            # Remove any old items that are no longer relevant.
            if Keys.GEAR_DEFAULTS_KEY in user:
                gear_defaults_list = user[Keys.GEAR_DEFAULTS_KEY]
                gear_index = 0
                for gear in gear_defaults_list:
                    if Keys.ACTIVITY_TYPE_KEY in gear and gear[Keys.ACTIVITY_TYPE_KEY] == activity_type:
                        gear_defaults_list.pop(gear_index)
                    gear_index = gear_index + 1

            # Add the new item.
            gear = {}
            gear[Keys.ACTIVITY_TYPE_KEY] = activity_type
            gear[Keys.GEAR_NAME_KEY] = gear_name
            gear_defaults_list.append(gear)

            user[Keys.GEAR_DEFAULTS_KEY] = gear_defaults_list
            return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Gear management methods
    #

    def create_gear(self, user_id, gear_id, gear_type, gear_name, description, add_time, retire_time, last_updated_time):
        """Create method for gear."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if gear_id is None:
            raise Exception("Unexpected empty object: gear_id")
        if gear_type is None:
            raise Exception("Unexpected empty object: gear_type")
        if gear_name is None:
            raise Exception("Unexpected empty object: gear_name")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Find the gear list.
            gear_list = []
            if Keys.GEAR_KEY in user:
                gear_list = user[Keys.GEAR_KEY]

            # Make sure we don't already have an item with this ID.
            for gear in gear_list:
                if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                    return False

            # Update the gear list.
            new_gear = {}
            new_gear[Keys.GEAR_ID_KEY] = str(gear_id)
            new_gear[Keys.GEAR_TYPE_KEY] = gear_type
            new_gear[Keys.GEAR_NAME_KEY] = gear_name
            new_gear[Keys.GEAR_DESCRIPTION_KEY] = description
            new_gear[Keys.GEAR_ADD_TIME_KEY] = int(add_time)
            new_gear[Keys.GEAR_RETIRE_TIME_KEY] = int(retire_time)
            new_gear[Keys.GEAR_LAST_UPDATED_TIME_KEY] = int(last_updated_time)
            gear_list.append(new_gear)
            user[Keys.GEAR_KEY] = gear_list
            return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_gear(self, user_id):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)

            # If the user's document was found.
            if user is not None and Keys.GEAR_KEY in user:
                return user[Keys.GEAR_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_gear(self, user_id, gear_id, gear_type, gear_name, description, add_time, retire_time, updated_time):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if gear_id is None:
            raise Exception("Unexpected empty object: gear_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Is there any gear?
            if Keys.GEAR_KEY not in user:
                return False

            # Update the gear list.
            gear_list = user[Keys.GEAR_KEY]
            gear_index = 0
            for gear in gear_list:
                if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                    if gear_type is not None:
                        gear[Keys.GEAR_TYPE_KEY] = gear_type
                    if gear_name is not None:
                        gear[Keys.GEAR_NAME_KEY] = gear_name
                    if description is not None:
                        gear[Keys.GEAR_DESCRIPTION_KEY] = description
                    if add_time is not None:
                        gear[Keys.GEAR_ADD_TIME_KEY] = int(add_time)
                    if retire_time is not None:
                        gear[Keys.GEAR_RETIRE_TIME_KEY] = int(retire_time)
                    if updated_time is not None:
                        gear[Keys.GEAR_LAST_UPDATED_TIME_KEY] = int(updated_time)
                    gear_list.pop(gear_index)
                    gear_list.append(gear)
                    user[Keys.GEAR_KEY] = gear_list
                    return self.update_user_doc(user)
                gear_index = gear_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_gear(self, user_id, gear_id):
        """Delete method for the gear with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if gear_id is None:
            raise Exception("Unexpected empty object: gear_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Is there any gear?
            if Keys.GEAR_KEY not in user:
                return False

            # Update the gear list.
            gear_list = user[Keys.GEAR_KEY]
            gear_index = 0
            for gear in gear_list:
                if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                    gear_list.pop(gear_index)
                    user[Keys.GEAR_KEY] = gear_list
                    return self.update_user_doc(user)
                gear_index = gear_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_all_gear(self, user_id):
        """Delete method for the gear with the specified ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Update the gear list.
            if Keys.GEAR_KEY in user:
                user[Keys.GEAR_KEY] = []
                self.update_user_doc(user)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
        
    #
    # Management methods for gear service records
    #

    def create_service_record(self, user_id, gear_id, service_record_id, record_date, record_description):
        """Create method for gear service records."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if gear_id is None:
            raise Exception("Unexpected empty object: gear_id")
        if service_record_id is None:
            raise Exception("Unexpected empty object: service_record_id")
        if record_date is None:
            raise Exception("Unexpected empty object: record_date")
        if record_description is None:
            raise Exception("Unexpected empty object: record_description")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Is there any gear?
            if Keys.GEAR_KEY not in user:
                return False

            # Find the gear list.
            gear_list = user[Keys.GEAR_KEY]

            # Find the gear.
            for gear in gear_list:
                if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                    service_rec = {}
                    service_rec[Keys.SERVICE_RECORD_ID_KEY] = str(service_record_id)
                    service_rec[Keys.SERVICE_RECORD_DATE_KEY] = int(record_date)
                    service_rec[Keys.SERVICE_RECORD_DESCRIPTION_KEY] = record_description

                    service_history = []
                    if Keys.GEAR_SERVICE_HISTORY_KEY in gear:
                        service_history = gear[Keys.GEAR_SERVICE_HISTORY_KEY]
                    service_history.append(service_rec)
                    gear[Keys.GEAR_SERVICE_HISTORY_KEY] = service_history

                    return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_service_record(self, user_id, gear_id, service_record_id):
        """Delete method for the service record with the specified user and gear ID."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if gear_id is None:
            raise Exception("Unexpected empty object: gear_id")
        if service_record_id is None:
            raise Exception("Unexpected empty object: service_record_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return []

            # Is there any gear?
            if Keys.GEAR_KEY not in user:
                return []

            # Find the gear list.
            gear_list = user[Keys.GEAR_KEY]

            # Find the gear.
            for gear in gear_list:
                if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id) and Keys.GEAR_SERVICE_HISTORY_KEY in gear:
                    service_history = gear[Keys.GEAR_SERVICE_HISTORY_KEY]
                    record_index = 0
                    for service_record in service_history:
                        if Keys.SERVICE_RECORD_ID_KEY in service_record and service_record[Keys.SERVICE_RECORD_ID_KEY] == service_record_id:
                            service_history.pop(record_index)
                            gear[Keys.GEAR_SERVICE_HISTORY_KEY] = service_history
                            return self.update_user_doc(user)
                        record_index = record_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    #
    # Pace plan management methods
    #

    def create_pace_plan(self, user_id, plan_id, plan_name, plan_description, target_distance, target_distance_units, target_time, target_splits, target_splits_units, last_updated_time):
        """Create method for a pace plan associated with the specified user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if plan_id is None:
            raise Exception("Unexpected empty object: plan_id")
        if plan_name is None:
            raise Exception("Unexpected empty object: plan_name")
        if target_distance is None:
            raise Exception("Unexpected empty object: target_distance")
        if target_distance_units is None:
            raise Exception("Unexpected empty object: target_distance_units")
        if target_time is None:
            raise Exception("Unexpected empty object: target_time")
        if target_splits is None:
            raise Exception("Unexpected empty object: target_splits")
        if target_splits_units is None:
            raise Exception("Unexpected empty object: target_splits_units")
        if last_updated_time is None:
            raise Exception("Unexpected empty object: last_updated_time")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Find the pace plans list.
            pace_plan_list = []
            if Keys.PACE_PLANS_KEY in user:
                pace_plan_list = user[Keys.PACE_PLANS_KEY]

            # Make sure we don't already have a pace plan with this ID.
            for pace_plan in pace_plan_list:
                if Keys.PACE_PLAN_ID_KEY in pace_plan and pace_plan[Keys.PACE_PLAN_ID_KEY] == str(plan_id):
                    return False

            # Update the pace plans list.
            new_pace_plan = {}
            new_pace_plan[Keys.PACE_PLAN_ID_KEY] = str(plan_id)
            new_pace_plan[Keys.PACE_PLAN_NAME_KEY] = plan_name
            new_pace_plan[Keys.PACE_PLAN_DESCRIPTION_KEY] = plan_description
            new_pace_plan[Keys.PACE_PLAN_TARGET_DISTANCE_KEY] = float(target_distance)
            new_pace_plan[Keys.PACE_PLAN_TARGET_DISTANCE_UNITS_KEY] = target_distance_units
            new_pace_plan[Keys.PACE_PLAN_TARGET_TIME_KEY] = target_time
            new_pace_plan[Keys.PACE_PLAN_TARGET_SPLITS_KEY] = int(float(target_splits))
            new_pace_plan[Keys.PACE_PLAN_TARGET_SPLITS_UNITS_KEY] = target_splits_units
            new_pace_plan[Keys.PACE_PLAN_LAST_UPDATED_KEY] = int(last_updated_time)
            pace_plan_list.append(new_pace_plan)
            user[Keys.PACE_PLANS_KEY] = pace_plan_list
            return self.update_user_doc(user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_pace_plans(self, user_id):
        """Retrieve method for pace plans associated with the specified user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return []

            # Are there any pace plans?
            if Keys.PACE_PLANS_KEY not in user:
                return []

            # Read the pace plans list.
            return user[Keys.PACE_PLANS_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_pace_plan(self, user_id, plan_id, plan_name, plan_description, target_distance, target_distance_units, target_time, target_splits, target_splits_units, last_updated_time):
        """Update method for a pace plan associated with the specified user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if plan_id is None:
            raise Exception("Unexpected empty object: plan_id")
        if plan_name is None:
            raise Exception("Unexpected empty object: plan_name")
        if plan_description is None:
            raise Exception("Unexpected empty object: plan_description")
        if target_distance is None:
            raise Exception("Unexpected empty object: target_distance")
        if target_distance_units is None:
            raise Exception("Unexpected empty object: target_distance_units")
        if target_time is None:
            raise Exception("Unexpected empty object: target_time")
        if target_splits is None:
            raise Exception("Unexpected empty object: target_splits")
        if target_splits_units is None:
            raise Exception("Unexpected empty object: target_splits_units")
        if last_updated_time is None:
            raise Exception("Unexpected empty object: last_updated_time")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Are there any pace plans?
            if Keys.PACE_PLANS_KEY not in user:
                return False

            # Update the pace plans list.
            pace_plan_list = user[Keys.PACE_PLANS_KEY]
            pace_plan_index = 0
            for pace_plan in pace_plan_list:
                if Keys.PACE_PLAN_ID_KEY in pace_plan and pace_plan[Keys.PACE_PLAN_ID_KEY] == str(plan_id):
                    pace_plan[Keys.PACE_PLAN_NAME_KEY] = plan_name
                    pace_plan[Keys.PACE_PLAN_DESCRIPTION_KEY] = plan_description
                    pace_plan[Keys.PACE_PLAN_TARGET_DISTANCE_KEY] = float(target_distance)
                    pace_plan[Keys.PACE_PLAN_TARGET_DISTANCE_UNITS_KEY] = target_distance_units
                    pace_plan[Keys.PACE_PLAN_TARGET_TIME_KEY] = target_time
                    pace_plan[Keys.PACE_PLAN_TARGET_SPLITS_KEY] = int(float(target_splits))
                    pace_plan[Keys.PACE_PLAN_TARGET_SPLITS_UNITS_KEY] = target_splits_units
                    pace_plan[Keys.PACE_PLAN_LAST_UPDATED_KEY] = int(last_updated_time)
                    pace_plan_list.pop(pace_plan_index)
                    pace_plan_list.append(pace_plan)
                    user[Keys.PACE_PLANS_KEY] = pace_plan_list
                    return self.update_user_doc(user)
                pace_plan_index = pace_plan_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_pace_plan(self, user_id, pace_plan_id):
        """Delete method for a pace plan associated with the specified user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if pace_plan_id is None:
            raise Exception("Unexpected empty object: pace_plan_id")

        try:
            # Find the user's document.
            user = self.retrieve_user_doc_from_id(user_id)
            if user is None:
                return False

            # Are there any pace plans?
            if Keys.PACE_PLANS_KEY not in user:
                return False

            # Update the pace plans list.
            pace_plan_list = user[Keys.PACE_PLANS_KEY]
            pace_plan_index = 0
            for pace_plan in pace_plan_list:
                if Keys.PACE_PLAN_ID_KEY in pace_plan and pace_plan[Keys.PACE_PLAN_ID_KEY] == str(pace_plan_id):
                    pace_plan_list.pop(pace_plan_index)
                    user[Keys.PACE_PLANS_KEY] = pace_plan_list
                    return self.update_user_doc(user)
                pace_plan_index = pace_plan_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Deferred task management methods
    #

    def create_deferred_task(self, user_id, task_type, celery_task_id, internal_task_id, details, status):
        """Create method for tracking a deferred task, such as a file import or activity analysis."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if task_type is None:
            raise Exception("Unexpected empty object: task_type")
        if celery_task_id is None:
            raise Exception("Unexpected empty object: celery_task_id")
        if internal_task_id is None:
            raise Exception("Unexpected empty object: internal_task_id")
        if status is None:
            raise Exception("Unexpected empty object: status")

        try:
            # Make sure we're dealing with a string.
            user_id_str = str(user_id)

            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({ Keys.USER_ID_KEY: user_id_str })

            # If the user's tasks document was not found then create it.
            if user_tasks is None:
                post = { Keys.USER_ID_KEY: user_id }
                insert_into_collection(self.tasks_collection, post)
                user_tasks = self.tasks_collection.find_one({ Keys.USER_ID_KEY: user_id_str })

            # If the user's tasks document was found.
            if user_tasks is not None:

                # Get the list of existing tasks.
                deferred_tasks = []
                if Keys.TASKS_KEY in user_tasks:
                    deferred_tasks = user_tasks[Keys.TASKS_KEY]

                # Create an entry for the new task.
                task = {}
                task[Keys.TASK_CELERY_ID_KEY] = str(celery_task_id)
                task[Keys.TASK_INTERNAL_ID_KEY] = str(internal_task_id)
                task[Keys.TASK_TYPE_KEY] = task_type
                task[Keys.TASK_DETAILS_KEY] = details
                task[Keys.TASK_STATUS_KEY] = status

                # Append it to the list.
                deferred_tasks.append(task)
                user_tasks[Keys.TASKS_KEY] = deferred_tasks

                # Update the database.
                return update_collection(self.tasks_collection, user_tasks)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_deferred_tasks(self, user_id):
        """Retrieve method for returning all the deferred tasks for a given user."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Make sure we're dealing with a string.
            user_id_str = str(user_id)

            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({ Keys.USER_ID_KEY: user_id_str })

            # If the user's tasks document was found.
            if user_tasks is not None and Keys.TASKS_KEY in user_tasks:
                return user_tasks[Keys.TASKS_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_deferred_task(self, user_id, internal_task_id, activity_id, status):
        """Updated method for deferred task status."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")
        if internal_task_id is None:
            raise Exception("Unexpected empty object: internal_task_id")
        if status is None:
            raise Exception("Unexpected empty object: status")

        try:
            # Make sure we're dealing with strings.
            user_id_str = str(user_id)
            internal_task_id_str = str(internal_task_id)

            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({ Keys.USER_ID_KEY: user_id_str })

            # If the user's tasks document was found.
            if user_tasks is not None and Keys.TASKS_KEY in user_tasks:

                # Find and update the record.
                for task in user_tasks[Keys.TASKS_KEY]:
                    if Keys.TASK_INTERNAL_ID_KEY in task and task[Keys.TASK_INTERNAL_ID_KEY] == internal_task_id_str:
                        task[Keys.TASK_ACTIVITY_ID_KEY] = activity_id
                        task[Keys.TASK_STATUS_KEY] = status
                        break

                # Update the database.
                return update_collection(self.tasks_collection, user_tasks)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_finished_deferred_tasks(self):
        """Delete method for removing deferred tasks that are completed."""
        try:
            # Find the user's tasks document.
            user_tasks_list = self.tasks_collection.find({})

            # For each user's task lists.
            for user_tasks in user_tasks_list:

                if Keys.TASKS_KEY in user_tasks:

                    # Find and update the record.
                    new_list = []
                    for task in user_tasks[Keys.TASKS_KEY]:
                        if task[Keys.TASK_STATUS_KEY] != Keys.TASK_STATUS_FINISHED:
                            new_list.append(task)
                    user_tasks[Keys.TASKS_KEY] = new_list

                    # Update the database.
                    update_collection(self.tasks_collection, user_tasks)

            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Uploaded file methods
    #

    def create_uploaded_file(self, activity_id, file_data):
        """Create method for an uploaded activity file."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")
        if file_data is None:
            raise Exception("Unexpected empty object: file_data")

        try:
            post = { Keys.ACTIVITY_ID_KEY: activity_id, Keys.UPLOADED_FILE_DATA_KEY: bytes(file_data) }
            return insert_into_collection(self.uploads_collection, post)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_uploaded_file(self, activity_id):
        """Delete method for an uploaded file associated with an activity."""
        if activity_id is None:
            raise Exception("Unexpected empty object: activity_id")

        try:
            deleted_result = self.uploads_collection.delete_one({ Keys.ACTIVITY_ID_KEY: str(activity_id) })
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # API key management methods
    #

    def retrieve_api_keys(self, user_id):
        """Retrieve method for API keys."""
        if user_id is None:
            raise Exception("Unexpected empty object: user_id")

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj}, { Keys.API_KEYS: 1 })

            # If the user was found.
            if user is not None and Keys.API_KEYS in user:
                return user[Keys.API_KEYS]
            return []
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    #
    # Admin methods
    #

    def enumerate_all_users(self, callback_func):
        if callback_func is None:
            raise Exception("Unexpected empty object: callback_func")

        try:
            # Get an iterator to the activities.
            users_cursor = self.users_collection.find({})

            # Iterate over the results, triggering the callback for each.
            if users_cursor is not None:
                try:
                    while users_cursor.alive:
                        user = users_cursor.next()
                        callback_func(user)
                except StopIteration:
                    pass
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
    
    def enumerate_all_activities(self, callback_func):
        if callback_func is None:
            raise Exception("Unexpected empty object: callback_func")

        try:
            # Things we don't need.
            exclude_keys = self.list_excluded_activity_keys()

            # Get an iterator to the activities.
            activities_cursor = self.activities_collection.find({}, exclude_keys)

            # Iterate over the results, triggering the callback for each.
            if activities_cursor is not None:
                try:
                    while activities_cursor.alive:
                        activity = activities_cursor.next()
                        callback_func(activity)
                except StopIteration:
                    pass
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Session token management methods
    #

    def create_session_token(self, token, user, expiry):
        """Create method for a session token."""
        if token is None:
            raise Exception("Unexpected empty object: token")
        if user is None:
            raise Exception("Unexpected empty object: user")
        if expiry is None:
            raise Exception("Unexpected empty object: expiry")

        try:
            post = { Keys.SESSION_TOKEN_KEY: token, Keys.SESSION_USER_KEY: user, Keys.SESSION_EXPIRY_KEY: expiry }
            return insert_into_collection(self.sessions_collection, post)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_session_data(self, token):
        """Retrieve method for session data."""
        if token is None:
            raise Exception("Unexpected empty object: token")

        try:
            session_data = self.sessions_collection.find_one({ Keys.SESSION_TOKEN_KEY: token })
            if session_data is not None:
                return session_data[Keys.SESSION_USER_KEY], session_data[Keys.SESSION_EXPIRY_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return (None, None)

    def delete_session_token(self, token):
        """Delete method for a session token."""
        if token is None:
            raise Exception("Unexpected empty object: token")

        try:
            deleted_result = self.sessions_collection.delete_one({ Keys.SESSION_TOKEN_KEY: token })
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
