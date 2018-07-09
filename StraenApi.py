# Copyright 2017 Michael J Simms
"""API request handlers"""

import json
import logging
import time
import urllib
import uuid
import Exporter
import StraenKeys

g_not_meta_data = ["DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy"]

class StraenApi(object):
    """Class for managing API messages."""

    def __init__(self, user_mgr, data_mgr, user_id):
        super(StraenApi, self).__init__()
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.user_id = user_id

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.debug(log_str)

    def parse_json_loc_obj(self, json_obj):
        """Helper function that parses the JSON object, which contains location data, and updates the database."""
        device_str = ""
        username = ""
        activity_type = ""
        activity_id_str = ""

        try:
            # Parse required identifiers.
            device_str = json_obj[StraenKeys.APP_DEVICE_ID_KEY]
            activity_id_str = json_obj[StraenKeys.APP_ID_KEY]

            # Parse optional identifiers.
            try:
                username = json_obj[StraenKeys.APP_USERNAME_KEY]
            except:
                pass
            try:
                activity_type = json_obj[StraenKeys.APP_TYPE_KEY]
            except:
                pass

            # Parse the metadata looking for the timestamp.
            date_time = int(time.time() * 1000)
            try:
                time_str = json_obj[StraenKeys.APP_TIME_KEY]
                date_time = int(time_str)
            except:
                pass

            # Parse the location data.
            try:
                lat = json_obj["Latitude"]
                lon = json_obj["Longitude"]
                alt = json_obj["Altitude"]
                self.data_mgr.create_location(device_str, activity_id_str, date_time, lat, lon, alt)
            except ValueError, e:
                self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
            except KeyError, e:
                self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
            except:
                self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))

            # Parse the rest of the data, which will be a combination of metadata and sensor data.
            for item in json_obj.iteritems():
                key = item[0]
                value = item[1]
                if not key in g_not_meta_data:
                    if key in [StraenKeys.APP_CADENCE_KEY, StraenKeys.APP_HEART_RATE_KEY, StraenKeys.APP_POWER_KEY]:
                        self.data_mgr.create_sensordata(activity_id_str, date_time, key, value)
                    elif key in [StraenKeys.APP_CURRENT_SPEED_KEY, StraenKeys.APP_CURRENT_PACE_KEY]:
                        self.data_mgr.create_metadata(activity_id_str, date_time, key, value, True)
        except ValueError, e:
            self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except KeyError, e:
            self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except:
            self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))
        return device_str, username, activity_type, activity_id_str

    def handle_update_location(self, values):
        """Called when an API message to update the location of a device is received."""
        if "locations" in values:
            locations = values["locations"]

            device_str = ""
            username = ""
            activity_type = ""
            activity_id_str = ""

            # Parse each of the location objects.
            for location_obj in locations:
                device_str, username, activity_type, activity_id_str = self.parse_json_loc_obj(location_obj)

            # Udpate the activity type.
            if len(activity_type) > 0:
                self.data_mgr.create_metadata(activity_id_str, 0, StraenKeys.ACTIVITY_TYPE_KEY, activity_type, False)

            # Update the user device association.
            if len(username) > 0:
                user_id, _, _ = self.user_mgr.retrieve_user(username)
                user_devices = self.user_mgr.retrieve_user_devices(user_id)
                if user_devices is not None and device_str not in user_devices:
                    self.user_mgr.create_user_device(user_id, device_str)
            return True, ""
        return False, ""

    def handle_login_submit(self, values):
        """Called when an API message to log in is received."""
        if self.user_id is not None:
            raise Exception("Already logged in.")

        if StraenKeys.USERNAME_KEY not in values:
            raise Exception("Username not specified.")
        if StraenKeys.PASSWORD_KEY not in values:
            raise Exception("Password not specified.")
        if StraenKeys.DEVICE_KEY not in values:
            raise Exception("Device ID not specified.")

        email = values[StraenKeys.USERNAME_KEY]
        password = values[StraenKeys.PASSWORD_KEY]
        device_str = values[StraenKeys.DEVICE_KEY]

        if not self.user_mgr.authenticate_user(email, password):
            raise Exception("Authentication failed.")

        return self.user_mgr.create_user_device(email, device_str), ""

    def handle_create_login_submit(self, values):
        """Called when an API message to create an account is received."""
        if self.user_id is not None:
            raise Exception("Already logged in.")

        if StraenKeys.USERNAME_KEY not in values:
            raise Exception("Username not specified.")
        if StraenKeys.PASSWORD1_KEY not in values:
            raise Exception("Password not specified.")
        if StraenKeys.PASSWORD2_KEY not in values:
            raise Exception("Password confirmation not specified.")
        if StraenKeys.DEVICE_KEY not in values:
            raise Exception("Device ID not specified.")
        if StraenKeys.REALNAME_KEY not in values:
            raise Exception("Real name not specified.")

        email = values[StraenKeys.USERNAME_KEY]
        password1 = values[StraenKeys.PASSWORD1_KEY]
        password2 = values[StraenKeys.PASSWORD2_KEY]
        device_str = values[StraenKeys.DEVICE_KEY]
        realname = values[StraenKeys.REALNAME_KEY]

        if not self.user_mgr.create_user(email, realname, password1, password2, device_str):
            raise Exception("User creation failed.")
        return True, ""

    def handle_update_email(self, values):
        """Updates the user's email address."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'email' not in values:
            raise Exception("Email not specified.")

        # Get the logged in user.
        current_username = self.user_mgr.get_logged_in_user()
        if current_username is None:
            raise Exception("Empty username.")

        # Decode the parameter.
        new_username = urllib.unquote_plus(values['email'])

        # Get the user details.
        user_id, _, user_realname = self.user_mgr.retrieve_user(current_username)

        # Update the user's password in the database.
        if not self.user_mgr.update_user_email(user_id, new_username, user_realname):
            raise Exception("Update failed.")
        return True, ""

    def handle_update_password(self, values):
        """Updates the user's email password."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'old_password' not in values:
            raise Exception("Old password not specified.")
        if 'new_password1' not in values:
            raise Exception("New password not specified.")
        if 'new_password2' not in values:
            raise Exception("New password confirmation not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise Exception("Empty username.")

        # Get the user details.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)

        # The the old and new passwords from the request.
        old_password = urllib.unquote_plus(values["old_password"])
        new_password1 = urllib.unquote_plus(values["new_password1"])
        new_password2 = urllib.unquote_plus(values["new_password2"])

        # Reauthenticate the user.
        if not self.user_mgr.authenticate_user(username, old_password):
            raise Exception("Authentication failed.")

        # Update the user's password in the database.
        if not self.user_mgr.update_user_password(user_id, username, user_realname, new_password1, new_password2):
            raise Exception("Update failed.")
        return True, ""

    def handle_delete_user(self, values):
        """Removes the user and all associated data."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if StraenKeys.PASSWORD_KEY not in values:
            raise Exception("Password not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise Exception("Empty username.")

        # Reauthenticate the user.
        password = values[StraenKeys.PASSWORD_KEY]
        if not self.user_mgr.authenticate_user(username, password):
            raise Exception("Authentication failed.")

        # Delete all the user's activities.
        self.data_mgr.delete_user_activities(self.user_id)

        # Delete the user.
        self.user_mgr.delete_user(self.user_id)
        return True, ""

    def handle_add_time_and_distance_activity(self, values):
        """Called when an API message to add a new activity based on time and distance is received."""
        if StraenKeys.APP_TIME_KEY not in values:
            raise Exception("Time not specified.")
        if StraenKeys.APP_DISTANCE_KEY not in values:
            raise Exception("Distance not specified.")

        activity_id_str = str(uuid.uuid4())
        return True, ""

    def handle_add_sets_and_reps_activity(self, values):
        """Called when an API message to add a new activity based on sets and reps is received."""
        if StraenKeys.APP_SETS_KEY not in values:
            raise Exception("Sets not specified.")

        activity_id_str = str(uuid.uuid4())
        sets = values[StraenKeys.APP_SETS_KEY]
        print sets
        return True, ""

    def handle_add_activity(self, values):
        """Called when an API message to add a new activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if StraenKeys.ACTIVITY_TYPE_KEY not in values:
            raise Exception("Activity type not specified.")

        switcher = {
            StraenKeys.TYPE_RUNNING_KEY : self.handle_add_time_and_distance_activity,
            StraenKeys.TYPE_CYCLING_KEY : self.handle_add_time_and_distance_activity,
            StraenKeys.TYPE_SWIMMING_KEY : self.handle_add_time_and_distance_activity,
            StraenKeys.TYPE_PULL_UPS_KEY : self.handle_add_sets_and_reps_activity
        }

        func = switcher.get(values[StraenKeys.ACTIVITY_TYPE_KEY], lambda: "Invalid activity type")
        return True, func(values)

    def handle_upload_activity_file(self, values):
        """Called when an API message to upload a file is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        return True, ""

    def handle_add_tag_to_activity(self, values):
        """Called when an API message to add a tag to an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        return True, ""

    def handle_delete_tag_from_activity(self, values):
        """Called when an API message to delete a tag from an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        return True, ""

    def handle_list_matched_users(self, values):
        """Called when an API message to list users is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'searchname' not in values:
            raise Exception("Invalid parameter.")

        search_name = values['searchname']
        search_name_len = len(search_name)
        if search_name_len < 3:
            raise Exception("Search name is too short.")
        if search_name_len > 100:
            raise Exception("Search name is too long.")

        matched_users = self.user_mgr.retrieve_matched_users(search_name)[:100] # Limit the number of results
        json_result = json.dumps(matched_users, ensure_ascii=False)
        return True, json_result

    def list_users_following(self, values):
        """Called when an API message to list the users you are following is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'target_email' not in values:
            raise Exception("Invalid parameter.")

        target_email = values['target_email']
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")

        users_following = self.user_mgr.list_users_followed(self.user_id)
        users_list_str = ""
        if users_following is not None and isinstance(users_following, list):
            users_list_str = str(users_following)
        return False, users_list_str

    def list_users_followed_by(self, values):
        """Called when an API message to list the users who are following you is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'target_email' not in values:
            raise Exception("Invalid parameter.")

        target_email = values['target_email']
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")

        users_followed_by = self.user_mgr.list_followers(self.user_id)
        users_list_str = ""
        if users_followed_by is not None and isinstance(users_followed_by, list):
            users_list_str = str(users_followed_by)
        return False, users_list_str

    def handle_request_to_follow(self, values):
        """Called when an API message request to follow another user is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'target_email' not in values:
            raise Exception("Invalid parameter.")

        target_email = values['target_email']
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")
        if self.user_mgr.request_to_follow(self.user_id, target_email):
            return True, ""
        return False, ""

    def handle_unfollow(self, values):
        """Called when an API message request to unfollow another user is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'target_email' not in values:
            raise Exception("Invalid parameter.")

        target_email = values['target_email']
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")
        return False, ""

    def handle_export_activity(self, values):
        """Called when an API message request to export an activity."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if StraenKeys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")

        exporter = Exporter.Exporter()
        result = exporter.export(self.data_mgr, values[StraenKeys.ACTIVITY_ID_KEY])
        return True, result

    def handle_claim_device(self, values):
        """Called when an API message request to associate a device with the logged in user is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'device_id' not in values:
            raise Exception("Invalid parameter.")

        result = self.user_mgr.create_user_device(self.user_id, values['device_id'])
        return result, ""

    def handle_create_tag(self, values):
        """Called when an API message create a tag is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if StraenKeys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if StraenKeys.ACTIVITY_TAGS_KEY not in values:
            raise Exception("Invalid parameter.")

        result = self.data_mgr.create_tag(values[StraenKeys.ACTIVITY_ID_KEY], values[StraenKeys.ACTIVITY_TAGS_KEY])
        return result, ""

    def handle_list_tags(self, values):
        """Called when an API message create list tags associated with an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if StraenKeys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")

        result = self.data_mgr.retrieve_tags(values[StraenKeys.ACTIVITY_ID_KEY])
        return result, ""

    def handle_api_1_0_request(self, args, values):
        """Called to parse a version 1.0 API message."""
        if len(args) <= 0:
            return False, ""

        request = args[0]
        json_values = json.loads(values)

        if request == 'update_location':
            return self.handle_update_location(json_values)
        elif request == 'login_submit':
            return self.handle_login_submit(json_values)
        elif request == 'create_login_submit':
            return self.handle_create_login_submit(json_values)
        elif request == 'update_email':
            return self.handle_update_email(json_values)
        elif request == 'update_password':
            return self.handle_update_password(json_values)
        elif request == 'delete_user':
            return self.handle_delete_user(json_values)
        elif request == 'add_activity':
            return self.handle_add_activity(json_values)
        elif request == 'upload_activity_file':
            return self.handle_upload_activity_file(json_values)
        elif request == 'add_tag_to_activity':
            return self.handle_add_tag_to_activity(json_values)
        elif request == 'delete_tag_from_activity':
            return self.handle_delete_tag_from_activity(json_values)
        elif request == 'list_matched_users':
            return self.handle_list_matched_users(json_values)
        elif request == 'list_users_following':
            return self.list_users_following(json_values)
        elif request == 'list_users_followed_by':
            return self.list_users_followed_by(json_values)
        elif request == 'request_to_follow':
            return self.handle_request_to_follow(json_values)
        elif request == 'unfollow':
            return self.handle_unfollow(json_values)
        elif request == 'export_activity':
            return self.handle_export_activity(json_values)
        elif request == 'claim_device':
            return self.handle_claim_device(json_values)
        elif request == 'create_tag':
            return self.handle_create_tag(json_values)
        elif request == 'list_tags':
            return self.handle_list_tags(json_values)
        return False, ""
