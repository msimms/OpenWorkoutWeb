# Copyright 2017 Michael J Simms

import bcrypt
import StraenDb


MIN_PASSWORD_LEN  = 8

class UserMgr(object):
    """Class for managing users"""

    def __init__(self, root_dir):
        self.database = StraenDb.MongoDatabase(root_dir)
        self.database.connect()
        super(UserMgr, self).__init__()

    def terminate(self):
        """Destructor"""
        self.database = None

    def authenticate_user(self, email, password):
        if self.database is None:
            return False, "No database."
        if len(email) == 0:
            return False, "An email address was not provided."
        if len(password) < MIN_PASSWORD_LEN:
            return False, "The password is too short."

        user_id, db_hash1, user_name = self.database.retrieve_user(email)
        if db_hash1 is None:
            return False, "The user could not be found."
        db_hash2 = bcrypt.hashpw(password.encode('utf-8'), db_hash1.encode('utf-8'))
        if db_hash1 == db_hash2:
            return True, "The user has been logged in."
        return False, "The password is invalid."

    def create_user(self, email, realname, password1, password2, device_str):
        if self.database is None:
            return False, "No database."
        if len(email) == 0:
            return False, "Email address not provided."
        if len(realname) == 0:
            return False, "Name not provided."
        if len(password1) < MIN_PASSWORD_LEN:
            return False, "The password is too short."
        if password1 != password2:
            return False, "The passwords do not match."
        if self.database.retrieve_user(email) is None:
            return False, "The user already exists."

        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(password1.encode('utf-8'), salt)
        if not self.database.create_user(email, realname, hash):
            return False, "An internal error was encountered when creating the user."

        if len(device_str) > 0:
            user_id, user_hash, user_realname = self.database.retrieve_user(email)
            self.database.create_user_device(user_id, device_str)

        return True, "The user was created."

    def create_user_device(self, email, device_str):
        if self.database is None:
            return False, "No database."
        if len(email) == 0:
            return False, "Email address not provided."
        if len(device_str) == 0:
            return False, "Device string not provided."

        user_id, _, _ = self.database.retrieve_user(email)
        self.database.create_user_device(user_id, device_str)

    def list_user_devices(self, user_id):
        if self.database is None:
            return False, "No database."
        if user_id is None or len(user_id) == 0:
            return False, "Bad parameter."
        return self.database.retrieve_user_devices(user_id)

    def list_users_followed(self, user_id):
        """Returns the user ids for all users that are followed by the user with the specified id."""
        if self.database is None:
            return False, "No database."
        if user_id is None or len(user_id) == 0:
            return False, "Bad parameter."
        return self.database.retrieve_users_followed(user_id)

    def list_followers(self, user_id):
        if self.database is None:
            return False, "No database."
        if user_id is None or len(user_id) == 0:
            return False, "Bad parameter."
        return self.database.retrieve_followers(user_id)

    def request_to_follow(self, email, following_name):
        if self.database is None:
            return False, "No database."
        if email is None or len(email) == 0:
            return False, "Bad parameter."
        if following_name is None or len(following_name) == 0:
            return False, "Bad parameter."
        return self.database.create_following_entry(email, following_name)

    def retrieve_user(self, email):
        """Retrieve method for a user."""
        if self.database is None:
            return False, "No database."
        if email is None or len(email) == 0:
            return False, "Bad parameter."
        return self.database.retrieve_user(email)

    def retrieve_matched_users(self, name):
        """Returns a list of user names for users that match the specified regex."""
        if self.database is None:
            return False, "No database."
        if name is None or len(name) == 0:
            return False, "Bad parameter."
        return self.database.retrieve_matched_users(name)
