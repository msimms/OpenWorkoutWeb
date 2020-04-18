# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Mike Simms
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
"""Manages user accounts"""

import bcrypt
import time
import Keys
import SessionMgr
import StraenDb


MIN_PASSWORD_LEN  = 8

class UserMgr(object):
    """Class for managing user accounts"""

    def __init__(self, session_mgr):
        self.database = StraenDb.MongoDatabase()
        self.database.connect()
        self.session_mgr = session_mgr
        super(UserMgr, self).__init__()

    def terminate(self):
        """Destructor"""
        self.database = None

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        return self.session_mgr.get_logged_in_user()

    def get_logged_in_user_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        return self.session_mgr.get_logged_in_user_from_cookie(auth_cookie)

    def create_new_session(self, username):
        """Starts a new session."""
        return self.session_mgr.create_new_session(username)

    def clear_session(self):
        """Ends the current session."""
        self.session_mgr.clear_session()

    def authenticate_user(self, email, password):
        """Validates a user against the credentials in the database."""
        if self.database is None:
            raise Exception("No database.")
        if len(email) == 0:
            raise Exception("An email address not provided.")
        if len(password) < MIN_PASSWORD_LEN:
            raise Exception("The password is too short.")

        _, db_hash1, _ = self.database.retrieve_user(email)
        if db_hash1 is None:
            raise Exception("The user could not be found.")
        db_hash2 = bcrypt.hashpw(password.encode('utf-8'), db_hash1.encode('utf-8'))
        if db_hash1 != db_hash2:
            raise Exception("The password is invalid.")
        return True

    def create_user(self, email, realname, password1, password2, device_str):
        """Adds a user to the database."""
        if self.database is None:
            raise Exception("No database.")
        if len(email) == 0:
            raise Exception("An email address not provided.")
        if len(realname) == 0:
            raise Exception("Name not provided.")
        if len(password1) < MIN_PASSWORD_LEN:
            raise Exception("The password is too short.")
        if password1 != password2:
            raise Exception("The passwords do not match.")
        if self.database.retrieve_user(email) is None:
            raise Exception("The user already exists.")

        salt = bcrypt.gensalt()
        computed_hash = bcrypt.hashpw(password1.encode('utf-8'), salt)
        if not self.database.create_user(email, realname, computed_hash):
            raise Exception("An internal error was encountered when creating the user.")

        if len(device_str) > 0:
            user_id, _, _ = self.database.retrieve_user(email)
            self.database.create_user_device(user_id, device_str)
        return True

    def retrieve_user_details(self, email):
        """Retrieve method for a user."""
        if self.database is None:
            raise Exception("No database.")
        if email is None or len(email) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user_details(email)

    def retrieve_user(self, email):
        """Retrieve method for a user."""
        if self.database is None:
            raise Exception("No database.")
        if email is None or len(email) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user(email)

    def retrieve_user_from_id(self, user_id):
        """Retrieve method for a user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user_from_id(user_id)

    def retrieve_matched_users(self, name):
        """Returns a list of user names for users that match the specified regex."""
        if self.database is None:
            raise Exception("No database.")
        if name is None or len(name) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_matched_users(name)

    def update_user_email(self, user_id, email, realname):
        """Updates a user's database entry."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Unexpected empty object: user_id.")
        if len(email) == 0:
            raise Exception("Email address not provided.")
        if len(realname) == 0:
            raise Exception("Name not provided.")

        if not self.database.update_user(user_id, email, realname, None):
            raise Exception("An internal error was encountered when updating the user.")
        return True

    def update_user_password(self, user_id, email, realname, password1, password2):
        """Updates a user's password."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Unexpected empty object: user_id.")
        if len(email) == 0:
            raise Exception("Email address not provided.")
        if len(realname) == 0:
            raise Exception("Name not provided.")
        if len(password1) < MIN_PASSWORD_LEN:
            raise Exception("The password is too short.")
        if password1 != password2:
            raise Exception("The passwords do not match.")

        salt = bcrypt.gensalt()
        computed_hash = bcrypt.hashpw(password1.encode('utf-8'), salt)
        if not self.database.update_user(user_id, email, realname, computed_hash):
            raise Exception("An internal error was encountered when updating the user.")
        return True

    def delete_user(self, user_id):
        """Removes a user from the database."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.delete_user(user_id)

    def create_user_device(self, email, device_str):
        """Associates a device with a user."""
        if self.database is None:
            raise Exception("No database.")
        if email is None or len(email) == 0:
            raise Exception("Email address not provided.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Device string not provided.")
        user_id, _, _ = self.database.retrieve_user(email)
        return self.database.create_user_device(user_id, device_str)

    def create_user_device_for_user_id(self, user_id, device_str):
        """Associates a device with a user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("User ID not provided.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Device string not provided.")
        return self.database.create_user_device(user_id, device_str)

    def retrieve_user_devices(self, user_id):
        """Returns a list of all the devices associated with the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        devices = self.database.retrieve_user_devices(user_id)
        if devices is not None:
            devices = list(set(devices)) # De-duplicate
        return devices

    def retrieve_user_from_device(self, device_str):
        """Finds the user associated with the device."""
        if self.database is None:
            raise Exception("No database.")
        if device_str is None or len(device_str) == 0:
            raise Exception("Device string not provided.")
        return self.database.retrieve_user_from_device(device_str)

    def request_to_be_friends(self, user_id, target_id):
        """Appends a user to the pending friends list of the user with the specified id."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        if target_id is None or len(target_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.create_pending_friend_request(user_id, target_id)

    def list_pending_friends(self, user_id):
        """Returns the user ids for all users that are pending confirmation as friends of the specified user."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_pending_friends(user_id)

    def confirm_request_to_be_friends(self, user_id, target_id):
        """Takes a user to the pending friends list and adds them to the actual friends list."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        if target_id is None or len(target_id) == 0:
            raise Exception("Bad parameter.")

        if self.database.delete_pending_friend_request(user_id, target_id):
            return self.database.create_friend(user_id, target_id)
        return False

    def list_friends(self, user_id):
        """Returns the user ids for all users that are friends with the user with specified id."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_friends(user_id)

    def unfriend(self, user_id, target_id):
        """Removes the users from each other's friends lists."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None or len(user_id) == 0:
            raise Exception("Bad parameter.")
        if target_id is None or len(target_id) == 0:
            raise Exception("Bad parameter.")
        return self.database.delete_friend(user_id, target_id)

    def update_user_setting(self, user_id, key, value):
        """Create/update method for user preferences."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if value is None:
            raise Exception("Bad parameter.")
        return self.database.update_user_setting(user_id, key, value)

    def retrieve_user_setting(self, user_id, key):
        """Retrieve method for user preferences."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")

        result = self.database.retrieve_user_setting(user_id, key)
        if result is None:
            if key == Keys.DEFAULT_PRIVACY:
                result = Keys.ACTIVITY_VISIBILITY_PUBLIC
            elif key == Keys.PREFERRED_UNITS_KEY:
                result = Keys.UNITS_STANDARD_KEY
            elif key == Keys.GENDER_KEY:
                result = Keys.GENDER_MALE_KEY
            elif key == Keys.HEIGHT_KEY:
                result = Keys.DEFAULT_HEIGHT
            elif key == Keys.WEIGHT_KEY:
                result = Keys.DEFAULT_WEIGHT
            elif key == Keys.BIRTHDAY_KEY:
                result = Keys.DEFAULT_BIRTHDAY
            elif key == Keys.GOAL_DATE_KEY:
                result = int(time.time())
            else:
                result = ""

        if isinstance(result, float):
            return result
        if isinstance(result, int):
            return result        
        return result.lower()

    def get_activity_user(self, activity):
        """Returns the user record that corresponds with the given activity."""
        if Keys.ACTIVITY_USER_ID_KEY in activity:
            username, realname = self.retrieve_user_from_id(activity[Keys.ACTIVITY_USER_ID_KEY])
            return activity[Keys.ACTIVITY_USER_ID_KEY], username, realname
        if Keys.ACTIVITY_DEVICE_STR_KEY in activity and len(activity[Keys.ACTIVITY_DEVICE_STR_KEY]) > 0:
            user = self.retrieve_user_from_device(activity[Keys.ACTIVITY_DEVICE_STR_KEY])
            if user is not None:
                return str(user[Keys.DATABASE_ID_KEY]), user[Keys.USERNAME_KEY], user[Keys.REALNAME_KEY]
        return None, None, None
