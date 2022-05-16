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
import DatabaseException
import InputChecker
import Keys
import Perf
import Workout

def insert_into_collection(collection, doc):
    """Handles differences in document insertion between pymongo 3 and 4."""
    if int(pymongo.__version__[0]) < 4:
        collection.insert(doc)
    else:
        collection.insert_one(doc)

def update_collection(collection, doc):
    """Handles differences in document updates between pymongo 3 and 4."""
    if int(pymongo.__version__[0]) < 4:
        collection.save(doc)
    else:
        query = { Keys.DATABASE_ID_KEY: doc[Keys.DATABASE_ID_KEY] }
        new_values = { "$set": doc }
        collection.update_one(query, new_values)

def update_activities_collection(self, activity):
    """Handles differences in document updates between pymongo 3 and 4 with activities collection-specific logic."""
    activity[Keys.ACTIVITY_LAST_UPDATED_KEY] = time.time()
    update_collection(self.activities_collection, activity)

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
    sessoins_collection = None

    def __init__(self):
        Database.Database.__init__(self)

    def connect(self, config):
        """Connects/creates the database"""
        try:
            # If we weren't given a database URL then assume localhost and default port.
            database_url = config.get_database_url()
            self.conn = pymongo.MongoClient('mongodb://' + database_url + '/?uuidRepresentation=pythonLegacy')

            # Database. Try the old name, if not found then create or open it with the new name.
            db_names = self.conn.list_database_names()
            if 'straendb' in db_names:
                self.database = self.conn['straendb']
            else:
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

    def list_excluded_activity_keys_activity_lists(self):
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
            post = { Keys.USERNAME_KEY: username, Keys.REALNAME_KEY: realname, Keys.HASH_KEY: passhash, Keys.DEVICES_KEY: [], Keys.FRIENDS_KEY: [], Keys.DEFAULT_PRIVACY_KEY: Keys.ACTIVITY_VISIBILITY_PUBLIC }
            insert_into_collection(self.users_collection, post)
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
            return self.users_collection.find_one({ Keys.USERNAME_KEY: username })
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

    def retrieve_user_from_id(self, user_id):
        """Retrieve method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_from_id.__name__ + ": Unexpected empty object: user_id")
            return None, None

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
            self.log_error(MongoDatabase.retrieve_user_from_id.__name__ + ": Unexpected empty object: api_key")
            return None, None, None

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

    def update_user(self, user_id, username, realname, passhash):
        """Update method for a user."""
        if user_id is None:
            self.log_error(MongoDatabase.update_user.__name__ + ": Unexpected empty object: user_id")
            return False
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
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user was found.
            if user is not None:
                user[Keys.USERNAME_KEY] = username
                user[Keys.REALNAME_KEY] = realname
                if passhash is not None:
                    user[Keys.HASH_KEY] = passhash
                update_collection(self.users_collection, user)
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
            self.log_error(MongoDatabase.retrieve_matched_users.__name__ + ": Unexpected empty object: username")
            return user_list
        if len(username) == 0:
            self.log_error(MongoDatabase.retrieve_matched_users.__name__ + ": username is empty")
            return user_list

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

    #
    # Device management methods
    #

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
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # Read the devices list.
            devices = []
            if user is not None and Keys.DEVICES_KEY in user:
                devices = user[Keys.DEVICES_KEY]

            # Append the device to the devices list, if it is not already there.
            if device_str not in devices:
                devices.append(device_str)
                user[Keys.DEVICES_KEY] = devices
                update_collection(self.users_collection, user)
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
            result_keys = { Keys.DEVICES_KEY: 1 }
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj }, result_keys)

            # Read the devices list.
            if user is not None and Keys.DEVICES_KEY in user:
                return user[Keys.DEVICES_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user_from_device(self, device_str):
        """Finds the user associated with the device."""
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_user_from_device.__name__ + ": Unexpected empty object: device_str")
            return None
        if len(device_str) == 0:
            self.log_error(MongoDatabase.retrieve_user_from_device.__name__ + ": Device string not provided")
            return None

        try:
            return self.users_collection.find_one({ Keys.DEVICES_KEY: device_str })
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
            self.log_error(MongoDatabase.create_pending_friend_request.__name__ + ": Unexpected empty object: user_id")
            return False
        if target_id is None:
            self.log_error(MongoDatabase.create_pending_friend_request.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user whose friendship is being requested.
            user_id_obj = ObjectId(str(target_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user was found then add the target user to the pending friends list.
            if user is not None:
                pending_friends_list = []
                if Keys.FRIEND_REQUESTS_KEY in user:
                    pending_friends_list = user[Keys.FRIEND_REQUESTS_KEY]
                if user_id not in pending_friends_list:
                    pending_friends_list.append(user_id)
                    user[Keys.FRIEND_REQUESTS_KEY] = pending_friends_list
                    update_collection(self.users_collection, user)
                    return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_pending_friends(self, user_id):
        """Returns the user ids for all users that are pending confirmation as friends of the specified user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_pending_friends.__name__ + ": Unexpected empty object: user_id")
            return []

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
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

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
            self.log_error(MongoDatabase.delete_pending_friend_request.__name__ + ": Unexpected empty object: user_id")
            return False
        if target_id is None:
            self.log_error(MongoDatabase.delete_pending_friend_request.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user whose friendship is being requested.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user was found then add the target user to the pending friends list.
            if user is not None:
                pending_friends_list = []
                if Keys.FRIEND_REQUESTS_KEY in user:
                    pending_friends_list = user[Keys.FRIEND_REQUESTS_KEY]
                if target_id in pending_friends_list:
                    pending_friends_list.remove(target_id)
                    user[Keys.FRIEND_REQUESTS_KEY] = pending_friends_list
                    update_collection(self.users_collection, user)
                    return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def create_friend(self, user_id, target_id):
        """Appends a user to the friends list of the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.create_friend.__name__ + ": Unexpected empty object: user_id")
            return False
        if target_id is None:
            self.log_error(MongoDatabase.create_friend.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # Find the target user.
            target_user_id_obj = ObjectId(str(target_id))
            target_user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: target_user_id_obj })

            # If the users were found then add each other to their friends lists.
            if user is not None and target_user is not None:

                # Update the user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in user:
                    friends_list = user[Keys.FRIENDS_KEY]
                if target_id not in friends_list:
                    friends_list.append(target_id)
                    user[Keys.FRIENDS_KEY] = friends_list
                    update_collection(self.users_collection, user)

                # Update the target user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in target_user:
                    friends_list = target_user[Keys.FRIENDS_KEY]
                if user_id not in friends_list:
                    friends_list.append(user_id)
                    target_user[Keys.FRIENDS_KEY] = friends_list
                    update_collection(self.users_collection, target_user)

                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_friends(self, user_id):
        """Returns the user ids for all users that are friends with the user who has the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_friends.__name__ + ": Unexpected empty object: user_id")
            return []

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
            self.log_error(MongoDatabase.delete_friend.__name__ + ": Unexpected empty object: user_id")
            return False
        if target_id is None:
            self.log_error(MongoDatabase.delete_friend.__name__ + ": Unexpected empty object: target_id")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # Find the target user.
            target_user_id_obj = ObjectId(str(target_id))
            target_user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: target_user_id_obj })

            # If the users were found then add each other to their friends lists.
            if user is not None and target_user is not None:

                # Update the user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in user:
                    friends_list = user[Keys.FRIENDS_KEY]
                if target_id in friends_list:
                    friends_list.remove(target_id)
                    user[Keys.FRIENDS_KEY] = friends_list
                    update_collection(self.users_collection, user)

                # Update the target user's friends list.
                friends_list = []
                if Keys.FRIENDS_KEY in target_user:
                    friends_list = target_user[Keys.FRIENDS_KEY]
                if user_id in friends_list:
                    friends_list.remove(user_id)
                    target_user[Keys.FRIENDS_KEY] = friends_list
                    update_collection(self.users_collection, target_user)

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
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: user_id")
            return False
        if key is None:
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: key")
            return False
        if value is None:
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: value")
            return False
        if update_time is None:
            self.log_error(MongoDatabase.update_user_setting.__name__ + ": Unexpected empty object: update_time")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user was found.
            if user is not None:

                # Do not replace a newer value with an older value.
                if Keys.USER_SETTINGS_LAST_UPDATED_KEY not in user:
                    user[Keys.USER_SETTINGS_LAST_UPDATED_KEY] = {}
                elif key in user[Keys.USER_SETTINGS_LAST_UPDATED_KEY] and user[Keys.USER_SETTINGS_LAST_UPDATED_KEY][key] > update_time:
                    return False

                # Update.
                user[Keys.USER_SETTINGS_LAST_UPDATED_KEY][key] = update_time
                user[key] = value
                update_collection(self.users_collection, user)
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
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # Find the setting.
            if user is not None and key in user and key in Keys.USER_SETTINGS:
                return user[key]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_user_settings(self, user_id, keys):
        """Retrieve method for user preferences."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_settings.__name__ + ": Unexpected empty object: user_id")
            return None
        if keys is None:
            self.log_error(MongoDatabase.retrieve_user_settings.__name__ + ": Unexpected empty object: keys")
            return None

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # Find the settings.
            results = []
            if user is not None:
                for key in keys:
                    if key in user and key in Keys.USER_SETTINGS:
                        results.append({key: user[key]})
                return results
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    #
    # Personal record management methods
    #

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
            user_id_str = str(user_id)
            user_records = self.records_collection.find_one({ Keys.RECORDS_USER_ID: user_id_str })

            # If the collection was found.
            if user_records is None:
                post = { Keys.RECORDS_USER_ID: user_id_str, Keys.PERSONAL_RECORDS_KEY: records }
                insert_into_collection(self.records_collection, post)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def update_user_personal_records(self, user_id, records):
        """Create method for a user's personal record. These are the bests across all activities. Activity records are the bests for individual activities."""
        if user_id is None:
            self.log_error(MongoDatabase.update_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return False
        if records is None or len(records) == 0:
            self.log_error(MongoDatabase.update_user_personal_records.__name__ + ": Unexpected empty object: records")
            return False

        try:
            # Find the user's records collection.
            user_id_str = str(user_id)
            user_records = self.records_collection.find_one({ Keys.RECORDS_USER_ID: user_id_str })

            # If the collection was found.
            if user_records is not None:
                user_records[Keys.PERSONAL_RECORDS_KEY] = records
                update_collection(self.records_collection, user_records)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_all_user_personal_records(self, user_id):
        """Delete method for a user's personal record. Deletes the entire personal record cache."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_all_user_personal_records.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            # Delete the user's records collection.
            user_id_str = str(user_id)
            deleted_result = self.records_collection.delete_one({ Keys.RECORDS_USER_ID: user_id_str })
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
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: user_id")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_bests.__name__ + ": Invalid object: activity_id " + str(activity_id))
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
            user_records = self.records_collection.find_one({ Keys.RECORDS_USER_ID: user_id })
            if user_records is not None:
                bests[Keys.ACTIVITY_TYPE_KEY] = activity_type
                bests[Keys.ACTIVITY_START_TIME_KEY] = activity_time
                user_records[activity_id] = bests
                update_collection(self.records_collection, user_records)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_recent_activity_bests_for_user(self, user_id, cutoff_time):
        """Retrieve method for a user's activity records. Only activities more recent than the specified cutoff time will be returned."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_recent_activity_bests_for_user.__name__ + ": Unexpected empty object: user_id")
            return {}

        try:
            user_records = self.records_collection.find_one({ Keys.RECORDS_USER_ID: user_id })
            if user_records is not None:
                bests = {}
                for activity_id in user_records:
                    if InputChecker.is_uuid(activity_id):
                        activity_bests = user_records[activity_id]
                        if (cutoff_time is None) or (activity_bests[Keys.ACTIVITY_START_TIME_KEY] > cutoff_time):
                            bests[activity_id] = activity_bests
                return bests
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return {}

    def retrieve_bounded_activity_bests_for_user(self, user_id, cutoff_time_lower, cutoff_time_higher):
        """Retrieve method for a user's activity records. Only activities more recent than the specified cutoff time will be returned."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_bounded_activity_bests_for_user.__name__ + ": Unexpected empty object: user_id")
            return {}
        if cutoff_time_lower is None:
            self.log_error(MongoDatabase.retrieve_bounded_activity_bests_for_user.__name__ + ": Unexpected empty object: cutoff_time_lower")
            return {}
        if cutoff_time_higher is None:
            self.log_error(MongoDatabase.retrieve_bounded_activity_bests_for_user.__name__ + ": Unexpected empty object: cutoff_time_higher")
            return {}

        try:
            user_records = self.records_collection.find_one({ Keys.RECORDS_USER_ID: user_id })
            if user_records is not None:
                bests = {}
                for activity_id in user_records:
                    if InputChecker.is_uuid(activity_id):
                        activity_bests = user_records[activity_id]
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
            self.log_error(MongoDatabase.delete_activity_best_for_user.__name__ + ": Unexpected empty object: user_id")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.delete_activity_best_for_user.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.delete_activity_best_for_user.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False

        try:
            user_records = self.records_collection.find_one({ Keys.RECORDS_USER_ID: user_id })
            if user_records is not None:
                user_records.pop(activity_id, None)
                update_collection(self.records_collection, user_records)
                return True
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
            self.log_error(MongoDatabase.retrieve_user_activity_list.__name__ + ": Unexpected empty object: user_id")
            return []

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys_activity_lists()

            if start_time is None or end_time is None:
                return list(self.activities_collection.find({ "$and": [ { Keys.ACTIVITY_USER_ID_KEY: { '$eq': user_id } } ]}, exclude_keys))
            return list(self.activities_collection.find({ "$and": [ { Keys.ACTIVITY_USER_ID_KEY: { '$eq': user_id }}, { Keys.ACTIVITY_START_TIME_KEY: { '$gt': start_time } }, { Keys.ACTIVITY_START_TIME_KEY: { '$lt': end_time } } ]}, exclude_keys))
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    @Perf.statistics
    def retrieve_each_user_activity(self, context, user_id, callback_func, return_all_data):
        """Retrieves each user activity and calls the callback function for each one."""
        """Returns TRUE on success, FALSE if an error was encountered."""
        """If return_all_data is False then only metadata is returned."""
        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys_activity_lists()

            activities_cursor = self.activities_collection.find({ Keys.ACTIVITY_USER_ID_KEY: user_id }, exclude_keys)
            if activities_cursor is not None:
                while activities_cursor.alive:
                    activity = activities_cursor.next()
                    callback_func(context, activity, user_id)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    @Perf.statistics
    def retrieve_devices_activity_list(self, devices, start_time, end_time, return_all_data):
        """Retrieves the list of activities associated with the specified devices."""
        if devices is None:
            self.log_error(MongoDatabase.retrieve_devices_activity_list.__name__ + ": Unexpected empty object: devices")
            return []

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys_activity_lists()

            # Build part of the exptression while sanity checking the input.
            device_list = []
            for device_str in devices:
                if InputChecker.is_uuid(device_str):
                    device_list.append( { Keys.ACTIVITY_DEVICE_STR_KEY: {'$eq': device_str} } )

            if start_time is None or end_time is None:
                return list(self.activities_collection.find({ "$or": device_list }, exclude_keys))
            return list(self.activities_collection.find({ "$and": [ { "$or": device_list }, { Keys.ACTIVITY_START_TIME_KEY: { '$gt': start_time } }, { Keys.ACTIVITY_START_TIME_KEY: { '$lt': end_time } } ] }, exclude_keys))
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    @Perf.statistics
    def retrieve_each_device_activity(self, context, user_id, device_str, callback_func, return_all_data):
        """Retrieves each device activity and calls the callback function for each one."""
        """If return_all_data is False then only metadata is returned."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_each_device_activity.__name__ + ": Unexpected empty object: device_str")
            return None
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_each_device_activity.__name__ + ": Unexpected empty object: device_str")
            return None
        if callback_func is None:
            self.log_error(MongoDatabase.retrieve_each_device_activity.__name__ + ": Unexpected empty object: device_str")
            return None

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys_activity_lists()

            activities_cursor = self.activities_collection.find({ Keys.ACTIVITY_DEVICE_STR_KEY: device_str }, exclude_keys)
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
            self.log_error(MongoDatabase.retrieve_most_recent_activity_for_device.__name__ + ": Unexpected empty object: device_str")
            return None

        try:
            # Things we don't need.
            if return_all_data:
                exclude_keys = None
            else:
                exclude_keys = self.list_excluded_activity_keys_activity_lists()

            activity = self.activities_collection.find_one({ Keys.ACTIVITY_DEVICE_STR_KEY: device_str }, exclude_keys, sort=[( '_id', pymongo.DESCENDING )])
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity.__name__ + ": Invalid object: activity_id " + str(activity_id))
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
            # Make sure the activity name is a string.
            activty_name = str(activty_name)

            # Create the activity.
            post = { Keys.ACTIVITY_ID_KEY: activity_id, Keys.ACTIVITY_NAME_KEY: activty_name, Keys.ACTIVITY_START_TIME_KEY: date_time, Keys.ACTIVITY_DEVICE_STR_KEY: device_str, Keys.ACTIVITY_VISIBILITY_KEY: "public", Keys.ACTIVITY_LOCATIONS_KEY: [] }
            insert_into_collection(self.activities_collection, post)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    @Perf.statistics
    def retrieve_activity(self, activity_id):
        """Retrieve method for an activity, specified by the activity ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity.__name__ + ": Unexpected empty object: activity_id")
            return None
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.retrieve_activity.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return None

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
            self.log_error(MongoDatabase.retrieve_activity_small.__name__ + ": Unexpected empty object: activity_id")
            return None
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.retrieve_activity_small.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return None

        try:
            # Things we don't need.
            exclude_keys = self.list_excluded_activity_keys_activity_lists()

            # Find the activity.
            return self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: re.compile(activity_id, re.IGNORECASE) }, exclude_keys)
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.update_activity.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if not locations:
            self.log_error(MongoDatabase.update_activity.__name__ + ": Unexpected empty object: locations")
            return False

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
                update_activities_collection(self, activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity(self, activity_id):
        """Delete method for an activity, specified by the activity ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.delete_activity.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.delete_activity.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False

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
            self.log_error(MongoDatabase.activity_exists.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.activity_exists.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False

        try:
            return self.activities_collection.count_documents({ Keys.ACTIVITY_ID_KEY: activity_id }, limit = 1) != 0
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def list_activities_with_last_updated_times_before(self, user_id, last_modified_time):
        """Returns a list of activity IDs with last modified times greater than the date provided."""
        if user_id is None:
            self.log_error(MongoDatabase.list_activities_with_last_updated_times_before.__name__ + ": Unexpected empty object: user_id")
            return []
        if last_modified_time is None:
            self.log_error(MongoDatabase.list_activities_with_last_updated_times_before.__name__ + ": Unexpected empty object: last_modified_time")
            return []

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
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if not locations:
            self.log_error(MongoDatabase.create_activity_locations.__name__ + ": Unexpected empty object: locations")
            return False

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
                update_activities_collection(self, activity)
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.retrieve_activity_locations.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found and it has location data.
            if activity is not None and Keys.ACTIVITY_LOCATIONS_KEY in activity:
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
            self.log_error(MongoDatabase.create_activity_sensor_reading.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_sensor_reading.__name__ + ": Invalid object: activity_id " + str(activity_id))
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
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
                value_list = []

                # Get the existing list.
                if sensor_type in activity:
                    value_list = activity[sensor_type]

                time_value_pair = { str(date_time): float(value) }
                value_list.append(time_value_pair)
                value_list.sort(key=retrieve_time_from_time_value_pair)

                # Save the changes.
                activity[sensor_type] = value_list
                update_activities_collection(self, activity)
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_sensor_readings.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_activity_sensor_readings.__name__ + ": Unexpected empty object: sensor_type")
            return False
        if values is None:
            self.log_error(MongoDatabase.create_activity_sensor_readings.__name__ + ": Unexpected empty object: values")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
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
                update_activities_collection(self, activity)
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.retrieve_activity_sensor_readings.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found and if it has data for the specified sensor type.
            if activity is not None and sensor_type in activity:
                sensor_data = activity[sensor_type]
                sensor_data.sort(key=retrieve_time_from_time_value_pair)
                return sensor_data
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity_event(self, activity_id, event):
        """Inherited from ActivityWriter. 'events' is an array of dictionaries in which each dictionary describes an event."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_event.__name__ + ": Unexpected empty object: activity_id")
            return None
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_event.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return None
        if event is None:
            self.log_error(MongoDatabase.create_activity_event.__name__ + ": Unexpected empty object: event")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found and if it has data for the specified sensor type.
            if activity is not None:
                events_list = []

                # Get the existing list.
                if Keys.APP_EVENTS_KEY in activity:
                    events_list = activity[Keys.APP_EVENTS_KEY]

                # Update the list.
                events_list.append(event)

                # Save the changes.
                activity[Keys.APP_EVENTS_KEY] = events_list
                update_activities_collection(self, activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity_events(self, activity_id, events):
        """Inherited from ActivityWriter. 'events' is an array of dictionaries in which each dictionary describes an event."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_events.__name__ + ": Unexpected empty object: activity_id")
            return None
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_events.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return None
        if events is None:
            self.log_error(MongoDatabase.create_activity_events.__name__ + ": Unexpected empty object: events")
            return None

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found and if it has data for the specified sensor type.
            if activity is not None:
                events_list = []

                # Get the existing list.
                if Keys.APP_EVENTS_KEY in activity:
                    events_list = activity[Keys.APP_EVENTS_KEY]

                # Update the list.
                events_list.extend(events)

                # Save the changes.
                activity[Keys.APP_EVENTS_KEY] = events_list
                update_activities_collection(self, activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return None

    def create_or_update_activity_metadata(self, activity_id, date_time, key, value, create_list):
        """Create method for a piece of metaadata. When dealing with a list, will append values."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_or_update_activity_metadata.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_or_update_activity_metadata.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if date_time is None and create_list:
            self.log_error(MongoDatabase.create_or_update_activity_metadata.__name__ + ": Unexpected empty object: date_time")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_or_update_activity_metadata.__name__ + ": Unexpected empty object: key")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_or_update_activity_metadata.__name__ + ": Unexpected empty object: value")
            return False
        if create_list is None:
            self.log_error(MongoDatabase.create_or_update_activity_metadata.__name__ + ": Unexpected empty object: create_list")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:

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
                    update_activities_collection(self, activity)
                    return True

                # The metadata is a scalar, just make sure to only update it if it has actually changed or was previously non-existent.
                elif key not in activity or activity[key] != value:
                    activity[key] = value
                    update_activities_collection(self, activity)
                    return True

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
            self.log_error(MongoDatabase.create_or_update_activity_metadata_list.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_or_update_activity_metadata_list.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if key is None:
            self.log_error(MongoDatabase.create_or_update_activity_metadata_list.__name__ + ": Unexpected empty object: key")
            return False
        if values is None:
            self.log_error(MongoDatabase.create_or_update_activity_metadata_list.__name__ + ": Unexpected empty object: values")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
                value_list = []

                for value in values:
                    time_value_pair = { str(value[0]): float(value[1]) }
                    value_list.append(time_value_pair)

                value_list.sort(key=retrieve_time_from_time_value_pair)
                activity[key] = value_list
                update_activities_collection(self, activity)
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_sets_and_reps_data.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if sets is None:
            self.log_error(MongoDatabase.create_activity_sets_and_reps_data.__name__ + ": Unexpected empty object: sets")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
                activity[Keys.APP_SETS_KEY] = sets
                update_activities_collection(self, activity)
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
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if not accels:
            self.log_error(MongoDatabase.create_activity_accelerometer_reading.__name__ + ": Unexpected empty object: accels")
            return False

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
                update_activities_collection(self, activity)
                return True
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
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if summary_data is None:
            self.log_error(MongoDatabase.create_activity_summary.__name__ + ": Unexpected empty object: summary_data")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
                activity[Keys.ACTIVITY_SUMMARY_KEY] = summary_data
                update_activities_collection(self, activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity_summary(self, activity_id):
        """Delete method for activity summary data. Summary data is data computed from the raw data."""
        if activity_id is None:
            self.log_error(MongoDatabase.delete_activity_summary.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.delete_activity_summary.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None and Keys.ACTIVITY_SUMMARY_KEY in activity:

                # Currently left out for performance reasons.
                #activity[Keys.ACTIVITY_SUMMARY_KEY] = {}
                #update_activities_collection(self, activity)
                return True
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
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_tag.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if tag is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: tag")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
                data = []
                if Keys.ACTIVITY_TAGS_KEY in activity:
                    data = activity[Keys.ACTIVITY_TAGS_KEY]
                data.append(tag)
                activity[Keys.ACTIVITY_TAGS_KEY] = data
                update_activities_collection(self, activity)
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
            update_activities_collection(self, activity)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
        
    def create_tags_on_activity_by_id(self, activity_id, tags):
        """Adds a tag to the specified activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_tags_on_activity_by_id.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_tags_on_activity_by_id.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if tags is None:
            self.log_error(MongoDatabase.create_tags_on_activity_by_id.__name__ + ": Unexpected empty object: tags")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found then add the tags.
            if activity is not None:
                activity[Keys.ACTIVITY_TAGS_KEY] = tags
                update_activities_collection(self, activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_tag(self, activity_id, tag):
        """Deletes the specified tag from the activity with the given ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_tag.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if tag is None:
            self.log_error(MongoDatabase.create_tag.__name__ + ": Unexpected empty object: tag")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None and Keys.ACTIVITY_TAGS_KEY in activity:
                data = activity[Keys.ACTIVITY_TAGS_KEY]
                data.remove(tag)
                activity[Keys.ACTIVITY_TAGS_KEY] = data
                update_activities_collection(self, activity)
                return True
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
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if commenter_id is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: commenter_id")
            return False
        if comment is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + ": Unexpected empty object: comment")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:
                data = []
                if Keys.ACTIVITY_COMMENTS_KEY in activity:
                    data = activity[Keys.ACTIVITY_COMMENTS_KEY]
                entry_dict = { Keys.ACTIVITY_COMMENTER_ID_KEY: commenter_id, Keys.ACTIVITY_COMMENT_KEY: comment }
                entry_str = json.dumps(entry_dict)
                data.append(entry_str)
                activity[Keys.ACTIVITY_COMMENTS_KEY] = data
                update_activities_collection(self, activity)
                return True
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
            self.log_error(MongoDatabase.create_activity_photo.__name__ + ": Unexpected empty object: user_id")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_photo.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.create_activity_photo.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if photo_hash is None:
            self.log_error(MongoDatabase.create_activity_photo.__name__ + ": Unexpected empty object: photo_hash")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None:

                # Append the hash of the photo to the photos list.
                photos = []
                if Keys.ACTIVITY_PHOTOS_KEY in activity:
                    photos = activity[Keys.ACTIVITY_PHOTOS_KEY]
                photos.append(photo_hash)

                # Remove duplicates.
                photos = list(dict.fromkeys(photos))

                # Save the updated activity.
                activity[Keys.ACTIVITY_PHOTOS_KEY] = photos
                update_activities_collection(self, activity)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_activity_photo(self, activity_id, photo_id):
        """Deletes the specified tag from the activity with the given ID."""
        if activity_id is None:
            self.log_error(MongoDatabase.delete_activity_photo.__name__ + ": Unexpected empty object: activity_id")
            return False
        if not InputChecker.is_uuid(activity_id):
            self.log_error(MongoDatabase.delete_activity_photo.__name__ + ": Invalid object: activity_id " + str(activity_id))
            return False
        if photo_id is None:
            self.log_error(MongoDatabase.delete_activity_photo.__name__ + ": Unexpected empty object: photo_id")
            return False

        try:
            # Find the activity.
            activity = self.activities_collection.find_one({ Keys.ACTIVITY_ID_KEY: activity_id })

            # If the activity was found.
            if activity is not None and Keys.ACTIVITY_PHOTOS_KEY in activity:
                photos = activity[Keys.ACTIVITY_PHOTOS_KEY]
                photos.remove(photo_id)
                activity[Keys.ACTIVITY_PHOTOS_KEY] = photos
                update_activities_collection(self, activity)
                return True
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
            self.log_error(MongoDatabase.create_workout.__name__ + ": Unexpected empty object: user_id")
            return False
        if workout_obj is None:
            self.log_error(MongoDatabase.create_workout.__name__ + ": Unexpected empty object: workout_obj")
            return False

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

            # If the workouts document was not found then create it.
            if workouts_doc is None:
                post = {}
                post[Keys.WORKOUT_PLAN_USER_ID_KEY] = user_id
                post[Keys.WORKOUT_PLAN_CALENDAR_ID_KEY] = str(uuid.uuid4()) # Create a calendar ID
                post[Keys.WORKOUT_LIST_KEY] = []
                insert_into_collection(self.workouts_collection, post)
                workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

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
                update_collection(self.workouts_collection, workouts_doc)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_planned_workout(self, user_id, workout_id):
        """Retrieve method for the workout with the specified user and ID."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_planned_workout.__name__ + ": Unexpected empty object: user_id")
            return None
        if workout_id is None:
            self.log_error(MongoDatabase.retrieve_planned_workout.__name__ + ": Unexpected empty object: workout_id")
            return None

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

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
            self.log_error(MongoDatabase.retrieve_planned_workouts_for_user.__name__ + ": Unexpected empty object: user_id")
            return None

        workouts = []

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

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
            self.log_error(MongoDatabase.retrieve_planned_workouts_calendar_id_for_user.__name__ + ": Unexpected empty object: user_id")
            return None

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

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
            self.log_error(MongoDatabase.retrieve_planned_workouts_by_calendar_id.__name__ + ": Unexpected empty object: calendar_id")
            return None

        workouts = []

        try:
            # Find the user's document with the specified calendar ID.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_CALENDAR_ID_KEY: calendar_id })

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

    def update_planned_workouts_for_user(self, user_id, workout_objs):
        """Update method for a list of workout objects."""
        if user_id is None:
            self.log_error(MongoDatabase.update_planned_workouts_for_user.__name__ + ": Unexpected empty object: user_id")
            return False
        if workout_objs is None:
            self.log_error(MongoDatabase.update_planned_workouts_for_user.__name__ + ": Unexpected empty object: workout_objs")
            return False

        try:
            # Find the user's workouts document.
            workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

            # If the workouts document was not found then create it.
            if workouts_doc is None:
                post = {}
                post[Keys.WORKOUT_PLAN_USER_ID_KEY] = user_id
                post[Keys.WORKOUT_LIST_KEY] = []
                insert_into_collection(self.workouts_collection, post)
                workouts_doc = self.workouts_collection.find_one({ Keys.WORKOUT_PLAN_USER_ID_KEY: user_id })

            # If the workouts document was found.
            if workouts_doc is not None and Keys.WORKOUT_LIST_KEY in workouts_doc:

                # Update and save the document.
                workouts_doc[Keys.WORKOUT_LIST_KEY] = [ workout_obj.to_dict() for workout_obj in workout_objs ]
                update_collection(self.workouts_collection, workouts_doc)
                return True
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
                if Keys.WORKOUT_PLAN_USER_ID_KEY in workout_doc:
                    user_id = workout_doc[Keys.WORKOUT_PLAN_USER_ID_KEY]
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
            self.log_error(MongoDatabase.retrieve_gear_defaults.__name__ + ": Unexpected empty object: user_id")
            return []

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

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
            self.log_error(MongoDatabase.update_gear_defaults.__name__ + ": Unexpected empty object: user_id")
            return False
        if activity_type is None:
            self.log_error(MongoDatabase.update_gear_defaults.__name__ + ": Unexpected empty object: activity_type")
            return False
        if gear_name is None:
            self.log_error(MongoDatabase.update_gear_defaults.__name__ + ": Unexpected empty object: gear_name")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

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
                update_collection(self.users_collection, user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Gear management methods
    #

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
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

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
                new_gear[Keys.GEAR_DESCRIPTION_KEY] = gear_description
                new_gear[Keys.GEAR_ADD_TIME_KEY] = int(gear_add_time)
                new_gear[Keys.GEAR_RETIRE_TIME_KEY] = int(gear_retire_time)
                gear_list.append(new_gear)
                user[Keys.GEAR_KEY] = gear_list
                update_collection(self.users_collection, user)
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
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None and Keys.GEAR_KEY in user:
                return user[Keys.GEAR_KEY]
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_gear(self, user_id, gear_id, gear_type, gear_name, gear_description, gear_add_time, gear_retire_time):
        """Retrieve method for the gear with the specified ID."""
        if user_id is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: user_id")
            return False
        if gear_id is None:
            self.log_error(MongoDatabase.update_gear.__name__ + ": Unexpected empty object: gear_id")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

                # Update the gear list.
                gear_list = []
                if Keys.GEAR_KEY in user:
                    gear_list = user[Keys.GEAR_KEY]
                    gear_index = 0
                    for gear in gear_list:
                        if Keys.GEAR_ID_KEY in gear and gear[Keys.GEAR_ID_KEY] == str(gear_id):
                            if gear_type is not None:
                                gear[Keys.GEAR_TYPE_KEY] = gear_type
                            if gear_name is not None:
                                gear[Keys.GEAR_NAME_KEY] = gear_name
                            if gear_description is not None:
                                gear[Keys.GEAR_DESCRIPTION_KEY] = gear_description
                            if gear_add_time is not None:
                                gear[Keys.GEAR_ADD_TIME_KEY] = int(gear_add_time)
                            if gear_retire_time is not None:
                                gear[Keys.GEAR_RETIRE_TIME_KEY] = int(gear_retire_time)
                            gear_list.pop(gear_index)
                            gear_list.append(gear)
                            user[Keys.GEAR_KEY] = gear_list
                            update_collection(self.users_collection, user)
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
            return False
        if gear_id is None:
            self.log_error(MongoDatabase.delete_gear.__name__ + ": Unexpected empty object: gear_id")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

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
                            update_collection(self.users_collection, user)
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
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

                # Update the gear list.
                if Keys.GEAR_KEY in user:
                    user[Keys.GEAR_KEY] = []
                    update_collection(self.users_collection, user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
        
    def create_service_record(self, user_id, gear_id, service_record_id, record_date, record_description):
        """Create method for gear service records."""
        if user_id is None:
            self.log_error(MongoDatabase.create_service_record.__name__ + ": Unexpected empty object: user_id")
            return False
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
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

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

                            update_collection(self.users_collection, user)
                            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_service_record(self, user_id, gear_id, service_record_id):
        """Delete method for the service record with the specified user and gear ID."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_service_record.__name__ + ": Unexpected empty object: user_id")
            return False
        if gear_id is None:
            self.log_error(MongoDatabase.delete_service_record.__name__ + ": Unexpected empty object: gear_id")
            return False
        if service_record_id is None:
            self.log_error(MongoDatabase.delete_service_record.__name__ + ": Unexpected empty object: service_record_id")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

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

                                        update_collection(self.users_collection, user)
                                        return True

                                    record_index = record_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    #
    # Pace plan management methods
    #

    def create_pace_plan(self, user_id, plan_id, plan_name, target_pace_min_km, target_distance_kms, display_units_pace, display_units_distance, splits, last_updated_time):
        """Create method for a pace plan associated with the specified user."""
        if user_id is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: user_id")
            return False
        if plan_id is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: plan_id")
            return False
        if plan_name is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: plan_name")
            return False
        if target_pace_min_km is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: target_pace_min_km")
            return False
        if target_distance_kms is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: target_distance_kms")
            return False
        if display_units_pace is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: display_units_pace")
            return False
        if display_units_distance is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: display_units_distance")
            return False
        if splits is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: splits")
            return False
        if last_updated_time is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: last_updated_time")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

                # Fidn the pace plans list.
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
                new_pace_plan[Keys.PACE_PLAN_TARGET_PACE_KEY] = float(target_pace_min_km)
                new_pace_plan[Keys.PACE_PLAN_TARGET_DISTANCE_KEY] = float(target_distance_kms)
                new_pace_plan[Keys.PACE_PLAN_DISPLAY_UNITS_PACE_KEY] = int(float(display_units_pace))
                new_pace_plan[Keys.PACE_PLAN_DISPLAY_UNITS_DISTANCE_KEY] = int(float(display_units_distance))
                new_pace_plan[Keys.PACE_PLAN_SPLITS_KEY] = int(float(splits))
                new_pace_plan[Keys.PACE_PLAN_LAST_UPDATED_KEY] = int(last_updated_time)
                pace_plan_list.append(new_pace_plan)
                user[Keys.PACE_PLANS_KEY] = pace_plan_list
                update_collection(self.users_collection, user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_pace_plans(self, user_id):
        """Retrieve method for pace plans associated with the specified user."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_pace_plan.__name__ + ": Unexpected empty object: user_id")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

                # Read the pace plans list.
                pace_plan_list = []
                if Keys.PACE_PLANS_KEY in user:
                    pace_plan_list = user[Keys.PACE_PLANS_KEY]
                return pace_plan_list
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return []

    def update_pace_plan(self, user_id, plan_id, plan_name, target_pace_min_km, target_distance_kms, display_units_pace, display_units_distance, splits, last_updated_time):
        """Update method for a pace plan associated with the specified user."""
        if user_id is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: user_id")
            return False
        if plan_id is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: plan_id")
            return False
        if plan_name is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: plan_name")
            return False
        if target_pace_min_km is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: target_pace_min_km")
            return False
        if target_distance_kms is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: target_pace_min_km")
            return False
        if display_units_pace is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: display_units_pace")
            return False
        if display_units_distance is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: display_units_distance")
            return False
        if splits is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: splits")
            return False
        if last_updated_time is None:
            self.log_error(MongoDatabase.create_pace_plan.__name__ + ": Unexpected empty object: last_updated_time")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

                # Update the pace plans list.
                pace_plan_list = []
                if Keys.PACE_PLANS_KEY in user:
                    pace_plan_list = user[Keys.PACE_PLANS_KEY]
                    pace_plan_index = 0
                    for pace_plan in pace_plan_list:
                        if Keys.PACE_PLAN_ID_KEY in pace_plan and pace_plan[Keys.PACE_PLAN_ID_KEY] == str(plan_id):
                            pace_plan[Keys.PACE_PLAN_NAME_KEY] = plan_name
                            pace_plan[Keys.PACE_PLAN_TARGET_PACE_KEY] = float(target_pace_min_km)
                            pace_plan[Keys.PACE_PLAN_TARGET_DISTANCE_KEY] = float(target_distance_kms)
                            pace_plan[Keys.PACE_PLAN_DISPLAY_UNITS_PACE_KEY] = int(float(display_units_pace))
                            pace_plan[Keys.PACE_PLAN_DISPLAY_UNITS_DISTANCE_KEY] = int(float(display_units_distance))
                            pace_plan[Keys.PACE_PLAN_SPLITS_KEY] = int(float(splits))
                            pace_plan[Keys.PACE_PLAN_LAST_UPDATED_KEY] = int(last_updated_time)
                            pace_plan_list.pop(pace_plan_index)
                            pace_plan_list.append(pace_plan)
                            user[Keys.PACE_PLANS_KEY] = pace_plan_list
                            update_collection(self.users_collection, user)
                            return True
                        pace_plan_index = pace_plan_index + 1
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_pace_plan(self, user_id, pace_plan_id):
        """Delete method for a pace plan associated with the specified user."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_pace_plan.__name__ + ": Unexpected empty object: user_id")
            return False
        if pace_plan_id is None:
            self.log_error(MongoDatabase.update_pace_plan.__name__ + ": Unexpected empty object: pace_plan_id")
            return False

        try:
            # Find the user's document.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user's document was found.
            if user is not None:

                # Update the pace plans list.
                pace_plan_list = []
                if Keys.PACE_PLANS_KEY in user:
                    pace_plan_list = user[Keys.PACE_PLANS_KEY]
                    pace_plan_index = 0
                    for pace_plan in pace_plan_list:
                        if Keys.PACE_PLAN_ID_KEY in pace_plan and pace_plan[Keys.PACE_PLAN_ID_KEY] == str(pace_plan_id):
                            pace_plan_list.pop(pace_plan_index)
                            user[Keys.PACE_PLANS_KEY] = pace_plan_list
                            update_collection(self.users_collection, user)
                            return True
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
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: user_id")
            return False
        if task_type is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: task_type")
            return False
        if celery_task_id is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: celery_task_id")
            return False
        if internal_task_id is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: internal_task_id")
            return False
        if status is None:
            self.log_error(MongoDatabase.create_deferred_task.__name__ + ": Unexpected empty object: status")
            return False

        try:
            # Make sure we're dealing with a string.
            user_id_str = str(user_id)

            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({ Keys.DEFERRED_TASKS_USER_ID: user_id_str })

            # If the user's tasks document was not found then create it.
            if user_tasks is None:
                post = { Keys.DEFERRED_TASKS_USER_ID: user_id }
                insert_into_collection(self.tasks_collection, post)
                user_tasks = self.tasks_collection.find_one({ Keys.DEFERRED_TASKS_USER_ID: user_id_str })

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
                update_collection(self.tasks_collection, user_tasks)
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
            # Make sure we're dealing with a string.
            user_id_str = str(user_id)

            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({ Keys.DEFERRED_TASKS_USER_ID: user_id_str })

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
            self.log_error(MongoDatabase.update_deferred_task.__name__ + ": Unexpected empty object: user_id")
            return False
        if internal_task_id is None:
            self.log_error(MongoDatabase.update_deferred_task.__name__ + ": Unexpected empty object: internal_task_id")
            return False
        if status is None:
            self.log_error(MongoDatabase.update_deferred_task.__name__ + ": Unexpected empty object: status")
            return False

        try:
            # Make sure we're dealing with strings.
            user_id_str = str(user_id)
            internal_task_id_str = str(internal_task_id)

            # Find the user's tasks document.
            user_tasks = self.tasks_collection.find_one({ Keys.DEFERRED_TASKS_USER_ID: user_id_str })

            # If the user's tasks document was found.
            if user_tasks is not None and Keys.TASKS_KEY in user_tasks:

                # Find and update the record.
                for task in user_tasks[Keys.TASKS_KEY]:
                    if Keys.TASK_INTERNAL_ID_KEY in task and task[Keys.TASK_INTERNAL_ID_KEY] == internal_task_id_str:
                        task[Keys.TASK_ACTIVITY_ID_KEY] = activity_id
                        task[Keys.TASK_STATUS_KEY] = status
                        break

                # Update the database.
                update_collection(self.tasks_collection, user_tasks)
                return True
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

    def create_uploaded_file(self, activity_id, file_data):
        """Create method for an uploaded activity file."""
        if activity_id is None:
            self.log_error(MongoDatabase.create_uploaded_file.__name__ + ": Unexpected empty object: activity_id")
            return False
        if file_data is None:
            self.log_error(MongoDatabase.create_uploaded_file.__name__ + ": Unexpected empty object: file_data")
            return False

        try:
            post = { Keys.ACTIVITY_ID_KEY: activity_id, Keys.UPLOADED_FILE_DATA_KEY: bytes(file_data) }
            insert_into_collection(self.uploads_collection, post)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def delete_uploaded_file(self, activity_id):
        """Delete method for an uploaded file associated with an activity."""
        if activity_id is None:
            self.log_error(MongoDatabase.delete_uploaded_file.__name__ + ": Unexpected empty object: activity_id")
            return False

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

    def create_api_key(self, user_id, key, rate):
        """Create method for an API key."""
        if user_id is None:
            self.log_error(MongoDatabase.create_api_key.__name__ + ": Unexpected empty object: user_id")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_api_key.__name__ + ": Unexpected empty object: key")
            return False
        if rate is None:
            self.log_error(MongoDatabase.create_api_key.__name__ + ": Unexpected empty object: rate")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user was found.
            if user is not None:
                key_list = []
                if Keys.API_KEYS in user:
                    key_list = user[Keys.API_KEYS]
                key_dict = { Keys.API_KEY: str(key), Keys.API_KEY_RATE: int(rate) }
                key_list.append(key_dict)
                user[Keys.API_KEYS] = key_list
                update_collection(self.users_collection, user)
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_api_keys(self, user_id):
        """Retrieve method for API keys."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_api_keys.__name__ + ": Unexpected empty object: user_id")
            return None

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

    def delete_api_key(self, user_id, key):
        """Delete method for an API key."""
        if user_id is None:
            self.log_error(MongoDatabase.delete_api_key.__name__ + ": Unexpected empty object: user_id")
            return False
        if key is None:
            self.log_error(MongoDatabase.delete_api_key.__name__ + ": Unexpected empty object: key")
            return False

        try:
            # Find the user.
            user_id_obj = ObjectId(str(user_id))
            user = self.users_collection.find_one({ Keys.DATABASE_ID_KEY: user_id_obj })

            # If the user was found.
            if user is not None and Keys.API_KEYS in user:

                # Make sure we're dealing with a string.
                key_str = str(key)

                key_list = user[Keys.API_KEYS]
                for item in key_list:
                    if item[Keys.API_KEY] == key_str:
                        key_list.remove(item)
                        break
                user[Keys.API_KEYS] = key_list
                update_collection(self.users_collection, user)
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
            self.log_error(MongoDatabase.create_session_token.__name__ + ": Unexpected empty object: token")
            return False
        if user is None:
            self.log_error(MongoDatabase.create_session_token.__name__ + ": Unexpected empty object: user")
            return False
        if expiry is None:
            self.log_error(MongoDatabase.create_session_token.__name__ + ": Unexpected empty object: expiry")
            return False

        try:
            post = { Keys.SESSION_TOKEN_KEY: token, Keys.SESSION_USER_KEY: user, Keys.SESSION_EXPIRY_KEY: expiry }
            insert_into_collection(self.sessions_collection, post)
            return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_session_data(self, token):
        """Retrieve method for session data."""
        if token is None:
            self.log_error(MongoDatabase.retrieve_session_data.__name__ + ": Unexpected empty object: token")
            return (None, None)

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
            self.log_error(MongoDatabase.delete_session_token.__name__ + ": Unexpected empty object: token")
            return False

        try:
            deleted_result = self.sessions_collection.delete_one({ Keys.SESSION_TOKEN_KEY: token })
            if deleted_result is not None:
                return True
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return False
