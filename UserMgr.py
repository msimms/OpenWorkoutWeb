# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Michael J Simms
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
import datetime
import time
import AppDatabase
import FtpCalculator
import Keys


MIN_PASSWORD_LEN  = 8

class UserMgr(object):
    """Class for managing user accounts"""

    def __init__(self, *, config, session_mgr):
        """Constructor"""
        assert config is not None
        self.session_mgr = session_mgr
        self.database = AppDatabase.MongoDatabase()
        self.database.connect(config)
        super(UserMgr, self).__init__()

    def terminate(self):
        """Destructor"""
        self.database = None

    def get_logged_in_username(self):
        """Returns the username associated with the current session."""
        return self.session_mgr.get_logged_in_username()

    def get_logged_in_user_id(self):
        """Returns the username associated with the current session."""
        logged_in_user_id = None
        logged_in_username = self.session_mgr.get_logged_in_username()
        if logged_in_username is not None:
            logged_in_user_id, _, _ = self.retrieve_user(logged_in_username)
        return logged_in_user_id

    def get_logged_in_username_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        return self.session_mgr.get_logged_in_username_from_cookie(auth_cookie)

    def create_new_session(self, username):
        """Starts a new session. Returns the session cookie and it's expiry date."""
        return self.session_mgr.create_new_session(username)

    def clear_current_session(self):
        """Ends the current session."""
        self.session_mgr.clear_current_session()

    def authenticate_user(self, email, password):
        """Validates a user against the credentials in the database."""
        if self.database is None:
            raise Exception("No database.")
        if len(email) == 0:
            raise Exception("An email address not provided.")
        if len(password) < MIN_PASSWORD_LEN:
            raise Exception("The password is too short.")

        # Get the exsting password hash for the user.
        _, db_hash1, _ = self.database.retrieve_user(email)
        if db_hash1 is None:
            raise Exception("The user (" + email + ") could not be found.")

        # Validate the provided password against the hash from the database.
        if isinstance(password, str):
            password = password.encode()
        if isinstance(db_hash1, str):
            db_hash1 = db_hash1.encode()
        return bcrypt.checkpw(password, db_hash1)

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
        
        # Make sure this user doesn't already exist.
        _, db_hash1, _ = self.database.retrieve_user(email)
        if db_hash1 is not None:
            raise Exception("The user already exists.")

        # Generate the salted hash of the password.
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

    def retrieve_user_from_api_key(self, api_key):
        """Retrieve method for a user."""
        if self.database is None:
            raise Exception("No database.")
        if api_key is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_user_from_api_key(api_key)

    def retrieve_matched_users(self, name):
        """Returns a list of user names for users that match the specified regex."""
        if self.database is None:
            raise Exception("No database.")
        if name is None or len(name) == 0:
            raise Exception("Bad parameter.")
        return self.database.retrieve_matched_users(name)

    def retrieve_random_user(self):
        """Returns a random user id and name from the database."""
        if self.database is None:
            raise Exception("No database.")
        return self.database.retrieve_random_user()

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

    def retrieve_user_from_activity(self, activity):
        """Given an activity object, determines the user."""
        if self.database is None:
            raise Exception("No database.")
        if activity is None:
            raise Exception("No activity object.")
        
        if Keys.ACTIVITY_USER_ID_KEY in activity:
            return activity[Keys.ACTIVITY_USER_ID_KEY]
        if Keys.ACTIVITY_DEVICE_STR_KEY in activity:
            user_rec = self.retrieve_user_from_device(activity[Keys.ACTIVITY_DEVICE_STR_KEY])
            if user_rec is not None:
                return str(user_rec[Keys.DATABASE_ID_KEY])
        return None

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

    def update_user_setting(self, user_id, key, value, update_time):
        """Create/update method for user preferences."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")
        if value is None:
            raise Exception("Bad parameter.")
        return self.database.update_user_setting(user_id, key, value, update_time)

    def estimate_max_heart_rate(self, user_id):
        """Looks through the list of maximum heart rate values in the database"""
        """and returns the highest value from the last year."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        # Read the stored max heart rates out of the database.
        stored_max_hrs = self.database.retrieve_user_setting(user_id, Keys.ESTIMATED_MAX_HEART_RATE_LIST_KEY)
        if stored_max_hrs is None:
            return None

        # Only consider heart rate values from the last year.
        ONE_YEAR = (365.25 * 24.0 * 60.0 * 60.0)
        one_year_ago = int(time.time()) - ONE_YEAR
        recent_hrs = [v for k,v in stored_max_hrs.items() if int(k) >= one_year_ago]
        return max(recent_hrs)

    def estimate_ftp(self, user_id):
        """Looks through the list of 20 minute power bests in the database"""
        """and returns an FTP estimation using the highest value from the last year."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")

        # Read the stored 20 minute power bests out of the database.
        stored_20_min_power_bests = self.database.retrieve_user_setting(user_id, Keys.BEST_CYCLING_20_MINUTE_POWER_LIST_KEY)
        if stored_20_min_power_bests is None:
            return None

        # Only consider values from the last year.
        ONE_YEAR = (365.25 * 24.0 * 60.0 * 60.0)
        one_year_ago = int(time.time()) - ONE_YEAR
        recent_bests = [v for k,v in stored_20_min_power_bests.items() if int(k) >= one_year_ago]
        calc = FtpCalculator.FtpCalculator()
        return calc.estimate_ftp_from_20_min_power(max(recent_bests))

    def default_user_setting(self, key):
        """Returns the default value for the specified setting."""
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")

        if key.casefold() == Keys.DEFAULT_PRIVACY_KEY.casefold():
            return Keys.ACTIVITY_VISIBILITY_PUBLIC
        if key.casefold() == Keys.USER_PREFERRED_UNITS_KEY.casefold():
            return Keys.UNITS_STANDARD_KEY
        if key.casefold() == Keys.USER_PREFERRED_FIRST_DAY_OF_WEEK_KEY.casefold():
            return Keys.DAYS_OF_WEEK[0]
        if key.casefold() == Keys.USER_BIRTHDAY_KEY.casefold():
            return Keys.DEFAULT_BIRTHDAY_KEY
        if key.casefold() == Keys.USER_HEIGHT_KEY.casefold():
            return Keys.DEFAULT_HEIGHT_KEY
        if key.casefold() == Keys.USER_WEIGHT_KEY.casefold():
            return Keys.DEFAULT_WEIGHT_KEY
        if key.casefold() == Keys.USER_BIOLOGICAL_SEX_KEY.casefold():
            return Keys.BIOLOGICAL_MALE_KEY
        if key.casefold() == Keys.USER_RESTING_HEART_RATE_KEY.casefold():
            return 0
        if key.casefold() == Keys.USER_MAXIMUM_HEART_RATE_KEY.casefold():
            return 0
        if key.casefold() == Keys.ESTIMATED_MAX_HEART_RATE_KEY.casefold():
            return 0
        if key.casefold() == Keys.ESTIMATED_MAX_HEART_RATE_LIST_KEY.casefold():
            return {}
        if key.casefold() == Keys.BEST_CYCLING_20_MINUTE_POWER_LIST_KEY.casefold():
            return {}
        if key.casefold() == Keys.ESTIMATED_CYCLING_FTP_KEY.casefold():
            return 0
        if key.casefold() == Keys.PLAN_INPUT_GOAL_TYPE_KEY.casefold():
            return Keys.GOAL_TYPE_COMPLETION
        if key.casefold() == Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY.casefold():
            return 5
        if key.casefold() == Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY.casefold():
            return 5
        if key.casefold() == Keys.PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY.casefold():
            return "sunday"
        if key.casefold() == Keys.GEN_WORKOUTS_WHEN_RACE_CAL_IS_EMPTY.casefold():
            return True
        if key.casefold() == Keys.USER_CAN_UPLOAD_PHOTOS_KEY.casefold():
            return False
        if key.casefold() == Keys.USER_IS_ADMIN_KEY.casefold():
            return False
        if key.casefold() == Keys.USER_HAS_SWIMMING_POOL_ACCESS.casefold():
            return False
        if key.casefold() == Keys.USER_HAS_OPEN_WATER_SWIM_ACCESS.casefold():
            return False
        if key.casefold() == Keys.USER_HAS_BICYCLE.casefold():
            return False
        if key.casefold() == Keys.USER_PLAN_LAST_GENERATED_TIME.casefold():
            return datetime.datetime.fromtimestamp(0)
        if key.casefold() == Keys.USER_ACTIVITY_SUMMARY_CACHE_LAST_PRUNED.casefold():
            return datetime.datetime.fromtimestamp(0)
        raise Exception("Unknown user setting: " + str(key))

    def retrieve_user_setting(self, user_id, key):
        """Retrieve method for user preferences."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if key is None or len(key) == 0:
            raise Exception("Bad parameter.")

        # Are we looking for the estimated max heart rate, because that is computed rather than stored?
        if key == Keys.ESTIMATED_MAX_HEART_RATE_KEY:
            max_hr = self.estimate_max_heart_rate(user_id)
            return max_hr

        # Are we looking for the estimated FTP value, because that is computed rather than stored?
        if key == Keys.ESTIMATED_CYCLING_FTP_KEY:
            ftp = self.estimate_ftp(user_id)
            return ftp

        # What's in the database?
        result = self.database.retrieve_user_setting(user_id, key)

        # These are the default values:
        if result is None:
            result = self.default_user_setting(key)

        # Return numbers and bools now so that we can handle strings differently.
        if isinstance(result, float) or isinstance(result, int) or isinstance(result, bool) or isinstance(result, datetime.datetime):
            return result

        # Return all strings as lowercase, just to keep things simple.
        if type(result) != list and type(result) != dict:
            result = result.lower()

        return result

    def retrieve_user_settings(self, user_id, keys):
        """Retrieve method for user preferences."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        if keys is None or len(keys) == 0:
            raise Exception("Bad parameter.")

        results = []

        for key in keys:
            result = self.retrieve_user_setting(user_id, key)
            results.append({key:result})
        return results

    def retrieve_best_max_hr(self, user_id):
        """Returns either the user's specified maximum heart rate, or the calculated (estimated) max hr."""
        """The user specified heart rate takes priority over the estimation."""
        user_max_hr = self.retrieve_user_setting(user_id, Keys.USER_MAXIMUM_HEART_RATE_KEY)
        if user_max_hr is not None:
            return user_max_hr
        estimated_max_hr = self.retrieve_user_setting(user_id, Keys.ESTIMATED_MAX_HEART_RATE_KEY)
        return estimated_max_hr

    def retrieve_api_keys(self, user_id):
        """Retrieve method for the user's API keys."""
        if self.database is None:
            raise Exception("No database.")
        if user_id is None:
            raise Exception("Bad parameter.")
        return self.database.retrieve_api_keys(user_id)
