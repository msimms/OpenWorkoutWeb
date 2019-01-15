# Copyright 2017 Michael J Simms
"""API request handlers"""

import json
import logging
import os
import time
import urllib
import uuid
import Exporter
import InputChecker
import Keys

g_not_meta_data = ["DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy"]

class Api(object):
    """Class for managing API messages."""

    def __init__(self, user_mgr, data_mgr, temp_dir, user_id, root_url):
        super(Api, self).__init__()
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.temp_dir = temp_dir
        self.user_id = user_id
        self.root_url = root_url

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.debug(log_str)

    def parse_json_loc_obj(self, activity_id, json_obj):
        """Helper function that parses the JSON object, which contains location data, and updates the database."""
        location = []

        try:
            # Parse the metadata for the timestamp.
            date_time = int(time.time() * 1000)
            if Keys.APP_TIME_KEY in json_obj:
                time_str = json_obj[Keys.APP_TIME_KEY]
                date_time = int(time_str)

            # Parse the location data.
            try:
                lat = json_obj[Keys.APP_LOCATION_LAT_KEY]
                lon = json_obj[Keys.APP_LOCATION_LON_KEY]
                alt = json_obj[Keys.APP_LOCATION_ALT_KEY]
                location = [date_time, lat, lon, alt]
            except ValueError, e:
                self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
            except KeyError, e:
                self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
            except:
                self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))

            # Parse the rest of the data, which will be a combination of metadata and sensor data.
            for item in json_obj.iteritems():
                key = item[0]
                if not key in g_not_meta_data:
                    if key in [Keys.APP_CADENCE_KEY, Keys.APP_HEART_RATE_KEY, Keys.APP_POWER_KEY]:
                        self.data_mgr.create_sensor_reading(activity_id, date_time, key, item[1])
                    elif key in [Keys.APP_CURRENT_SPEED_KEY, Keys.APP_CURRENT_PACE_KEY]:
                        self.data_mgr.create_metadata(activity_id, date_time, key, item[1], True)
        except ValueError, e:
            self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except KeyError, e:
            self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except:
            self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))
        return location

    def parse_json_accel_obj(self, activity_id, json_obj):
        """Helper function that parses the JSON object, which contains location data, and updates the database."""
        accel = []

        try:
            # Parse the metadata for the timestamp.
            date_time = int(time.time() * 1000)
            if Keys.APP_TIME_KEY in json_obj:
                time_str = json_obj[Keys.APP_TIME_KEY]
                date_time = int(time_str)

            x = json_obj[Keys.APP_AXIS_NAME_X]
            y = json_obj[Keys.APP_AXIS_NAME_Y]
            z = json_obj[Keys.APP_AXIS_NAME_Z]
            accel = [date_time, x, y, z]
        except ValueError, e:
            self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except KeyError, e:
            self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except:
            self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))
        return accel

    def handle_update_status(self, values):
        """Called when an API message to update the status of a device is received."""
        device_str = ""
        activity_id = ""
        activity_type = ""
        username = ""
        locations = []
        accels = []

        # Parse required identifiers.
        device_str = values[Keys.APP_DEVICE_ID_KEY]
        activity_id = values[Keys.APP_ID_KEY]

        # Parse optional identifiers.
        if Keys.APP_TYPE_KEY in values:
            activity_type = values[Keys.APP_TYPE_KEY]
        if Keys.APP_USERNAME_KEY in values:
            username = values[Keys.APP_USERNAME_KEY]

        if Keys.APP_LOCATIONS_KEY in values:

            # Parse each of the location objects.
            encoded_locations = values[Keys.APP_LOCATIONS_KEY]
            for location_obj in encoded_locations:
                location = self.parse_json_loc_obj(activity_id, location_obj)
                locations.append(location)

            # Update the locations.
            if locations:
                self.data_mgr.create_locations(device_str, activity_id, locations)

        if Keys.APP_ACCELEROMETER_KEY in values:

            # Parse each of the accelerometer objects.
            encoded_accel = values[Keys.APP_ACCELEROMETER_KEY]
            for accel_obj in encoded_accel:
                accel = self.parse_json_accel_obj(activity_id, accel_obj)
                accels.append(accel)

            # Update the accelerometer readings.
            if accels:
                self.data_mgr.create_accelerometer_reading(device_str, activity_id, accels)

        # Udpate the activity type.
        if len(activity_type) > 0:
            self.data_mgr.create_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, activity_type, False)

        # Update the user device association.
        if len(username) > 0:
            temp_user_id, _, _ = self.user_mgr.retrieve_user(username)
            if temp_user_id == self.user_id:
                user_devices = self.user_mgr.retrieve_user_devices(self.user_id)
                if user_devices is not None and device_str not in user_devices:
                    self.user_mgr.create_user_device_for_user_id(self.user_id, device_str)

        # Analysis is now obsolete, so delete it.
        self.data_mgr.delete_activity_summary(activity_id)

        return True, ""

    def handle_login_submit(self, values):
        """Called when an API message to log in is received."""
        if self.user_id is not None:
            return True, self.user_mgr.get_logged_in_user()

        if Keys.USERNAME_KEY not in values:
            raise Exception("Username not specified.")
        if Keys.PASSWORD_KEY not in values:
            raise Exception("Password not specified.")

        email = urllib.unquote_plus(values[Keys.USERNAME_KEY])
        if not InputChecker.is_email_address(email):
            raise Exception("Invalid email address.")
        password = urllib.unquote_plus(values[Keys.PASSWORD_KEY])

        if not self.user_mgr.authenticate_user(email, password):
            raise Exception("Authentication failed.")

        if Keys.DEVICE_KEY in values:
            device_str = urllib.unquote_plus(values[Keys.DEVICE_KEY])
            result = self.user_mgr.create_user_device(email, device_str)
        else:
            result = True

        cookie = self.user_mgr.create_new_session(email)
        return result, str(cookie)

    def handle_create_login_submit(self, values):
        """Called when an API message to create an account is received."""
        if self.user_id is not None:
            raise Exception("Already logged in.")

        if Keys.USERNAME_KEY not in values:
            raise Exception("Username not specified.")
        if Keys.REALNAME_KEY not in values:
            raise Exception("Real name not specified.")
        if Keys.PASSWORD1_KEY not in values:
            raise Exception("Password not specified.")
        if Keys.PASSWORD2_KEY not in values:
            raise Exception("Password confirmation not specified.")

        email = urllib.unquote_plus(values[Keys.USERNAME_KEY])
        if not InputChecker.is_email_address(email):
            raise Exception("Invalid email address.")
        realname = urllib.unquote_plus(values[Keys.REALNAME_KEY])
        password1 = urllib.unquote_plus(values[Keys.PASSWORD1_KEY])
        password2 = urllib.unquote_plus(values[Keys.PASSWORD2_KEY])

        if Keys.DEVICE_KEY in values:
            device_str = urllib.unquote_plus(values[Keys.DEVICE_KEY])
        else:
            device_str = ""

        if not self.user_mgr.create_user(email, realname, password1, password2, device_str):
            raise Exception("User creation failed.")

        cookie = self.user_mgr.create_new_session(email)
        return True, str(cookie)

    def handle_login_status(self, values):
        """Called when an API message to check the login status in is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        return True, ""

    def handle_logout(self, values):
        """Ends the session for the specified user."""
        if self.user_id is None:
            raise Exception("Not logged in.")

        # End the session
        self.user_mgr.clear_session()
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
        if Keys.PASSWORD_KEY not in values:
            raise Exception("Password not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise Exception("Empty username.")

        # Reauthenticate the user.
        password = urllib.unquote_plus(values[Keys.PASSWORD_KEY])
        if not self.user_mgr.authenticate_user(username, password):
            raise Exception("Authentication failed.")

        # Delete all the user's activities.
        self.data_mgr.delete_user_activities(self.user_id)

        # Delete the user.
        self.user_mgr.delete_user(self.user_id)
        return True, ""

    def handle_list_activities(self, values):
        """Removes the specified activity."""
        if self.user_id is None:
            raise Exception("Not logged in.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise Exception("Empty username.")

        # Get the user details.
        _, _, user_realname = self.user_mgr.retrieve_user(username)

        # Get the activiites that belong to the logged in user.
        matched_activities = []
        if Keys.FOLLOWING_KEY in values:
            activities = self.data_mgr.retrieve_all_activities_visible_to_user(self.user_id, user_realname, None, None)
        else:
            activities = self.data_mgr.retrieve_user_activity_list(self.user_id, user_realname, None, None)

        # Convert the activities list to an array of JSON objects for return to the client.
        if activities is not None and isinstance(activities, list):
            for activity in activities:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY
                activity_name = Keys.UNNAMED_ACTIVITY_TITLE
                if Keys.ACTIVITY_TYPE_KEY in activity:
                    activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
                if Keys.ACTIVITY_NAME_KEY in activity:
                    activity_name = activity[Keys.ACTIVITY_NAME_KEY]

                if Keys.ACTIVITY_TIME_KEY in activity and Keys.ACTIVITY_ID_KEY in activity:
                    url = self.root_url + "/activity/" + activity[Keys.ACTIVITY_ID_KEY]
                    temp_activity = {'title':'[' + activity_type + '] ' + activity_name, 'url':url, 'time':int(activity[Keys.ACTIVITY_TIME_KEY])}
                matched_activities.append(temp_activity)
        json_result = json.dumps(matched_activities, ensure_ascii=False)
        return True, json_result

    def handle_delete_activity(self, values):
        """Removes the specified activity."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Activity ID not specified.")

        # Get the device and activity IDs from the push request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        # Get the activiites that belong to the logged in user.
        activities = self.data_mgr.retrieve_user_activity_list(self.user_id, "", None, None)
        deleted = False
        for activity in activities:
            if Keys.ACTIVITY_ID_KEY in activity:
                if activity[Keys.ACTIVITY_ID_KEY] == activity_id:
                    self.data_mgr.delete_activity(activity['_id'])
                    deleted = True
                    break

        # Did we find it?
        if not deleted:
            raise Exception("An error occurred. Nothing deleted.")

        return True, ""

    def handle_add_time_and_distance_activity(self, values):
        """Called when an API message to add a new activity based on time and distance is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.APP_DISTANCE_KEY not in values:
            raise Exception("Distance not specified.")
        if Keys.APP_DURATION_KEY not in values:
            raise Exception("Duration not specified.")
        if Keys.ACTIVITY_TIME_KEY not in values:
            raise Exception("Activity start time not specified.")
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise Exception("Activity type not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise Exception("Empty username.")

        # Validate the activity start time.
        start_time = values[Keys.ACTIVITY_TIME_KEY]
        if not InputChecker.is_integer(start_time):
            raise Exception("Invalid start time.")

        # Add the activity to the database.
        activity_type = urllib.unquote_plus(values[Keys.ACTIVITY_TYPE_KEY])
        device_str, activity_id = self.data_mgr.create_activity(username, self.user_id, "", "", activity_type, int(start_time))
        self.data_mgr.create_metadata(activity_id, 0, Keys.APP_DISTANCE_KEY, float(values[Keys.APP_DISTANCE_KEY]), False)
        self.data_mgr.create_metadata(activity_id, 0, Keys.APP_DURATION_KEY, float(values[Keys.APP_DURATION_KEY]), False)

        return ""

    def handle_add_sets_and_reps_activity(self, values):
        """Called when an API message to add a new activity based on sets and reps is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.APP_SETS_KEY not in values:
            raise Exception("Sets not specified.")
        if Keys.ACTIVITY_TIME_KEY not in values:
            raise Exception("Activity start time not specified.")
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise Exception("Activity type not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise Exception("Empty username.")

        # Convert the array string to an actual array (note: I realize I could use eval for this, but that seems dangerous)
        sets = urllib.unquote_plus(values[Keys.APP_SETS_KEY])
        if len(sets) <= 2:
            raise Exception("Malformed set data.")
        sets = sets[1:-1] # Remove the brackets
        sets = sets.split(',')
        if len(sets) == 0:
            raise Exception("Set data was not specified.")

        # Make sure everything is a number.
        new_sets = []
        for current_set in sets:
            rep_count = int(current_set)
            if rep_count > 0:
                new_sets.append(rep_count)

        # Make sure we got at least one valid set.
        if len(new_sets) == 0:
            raise Exception("Set data was not specified.")

        # Validate the activity start time.
        start_time = values[Keys.ACTIVITY_TIME_KEY]
        if not InputChecker.is_integer(start_time):
            raise Exception("Invalid start time.")

        # Add the activity to the database.
        activity_type = urllib.unquote_plus(values[Keys.ACTIVITY_TYPE_KEY])
        device_str, activity_id = self.data_mgr.create_activity(username, self.user_id, "", "", activity_type, int(start_time))
        self.data_mgr.create_sets_and_reps_data(activity_id, new_sets)

        return ""

    def handle_add_activity(self, values):
        """Called when an API message to add a new activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise Exception("Activity type not specified.")

        activity_type = urllib.unquote_plus(values[Keys.ACTIVITY_TYPE_KEY])
        switcher = {
            Keys.TYPE_RUNNING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_CYCLING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_SWIMMING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_PULL_UPS_KEY : self.handle_add_sets_and_reps_activity,
            Keys.TYPE_PUSH_UPS_KEY : self.handle_add_sets_and_reps_activity
        }

        func = switcher.get(activity_type, lambda: "Invalid activity type")
        return True, func(values)

    def handle_upload_activity_file(self, username, values):
        """Called when an API message to upload a file is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.UPLOADED_FILE_NAME_KEY not in values:
            raise Exception("File name not specified.")
        if Keys.UPLOADED_FILE_DATA_KEY not in values:
            raise Exception("File data not specified.")

        # Decode the parameters.
        uploaded_file_name = urllib.unquote_plus(values[Keys.UPLOADED_FILE_NAME_KEY])
        uploaded_file_data = urllib.unquote_plus(values[Keys.UPLOADED_FILE_DATA_KEY])

        # Check for empty.
        if len(uploaded_file_name) == 0:
            raise Exception('Empty file name.')
        if len(uploaded_file_data) == 0:
            raise Exception('Empty file data for ' + uploaded_file_name + '.')

        # Parse the file and store it's contents in the database.
        self.data_mgr.import_file(username, self.user_id, uploaded_file_data, uploaded_file_name)

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

        search_name = urllib.unquote_plus(values['searchname'])
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

        users_following = self.user_mgr.list_users_followed(self.user_id)
        users_list_str = ""
        if users_following is not None and isinstance(users_following, list):
            users_list_str = str(users_following)
        return True, users_list_str

    def list_users_followed_by(self, values):
        """Called when an API message to list the users who are following you is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")

        users_followed_by = self.user_mgr.list_followers(self.user_id)
        users_list_str = ""
        if users_followed_by is not None and isinstance(users_followed_by, list):
            users_list_str = str(users_followed_by)
        return True, users_list_str

    def handle_request_to_follow(self, values):
        """Called when an API message request to follow another user is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.TARGET_EMAIL_KEY not in values:
            raise Exception("Invalid parameter.")

        target_email = urllib.unquote_plus(values[Keys.TARGET_EMAIL_KEY])
        if not InputChecker.is_email_address(target_email):
            raise Exception("Invalid email address.")

        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")
        if not self.user_mgr.request_to_follow(self.user_id, target_id):
            raise Exception("Request failed.")
        return True, ""

    def handle_unfollow(self, values):
        """Called when an API message request to unfollow another user is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.TARGET_EMAIL_KEY not in values:
            raise Exception("Invalid parameter.")

        target_email = urllib.unquote_plus(values[Keys.TARGET_EMAIL_KEY])
        if not InputChecker.is_email_address(target_email):
            raise Exception("Invalid email address.")

        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")
        return False, ""

    def handle_export_activity(self, values):
        """Called when an API message request to export an activity."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if Keys.ACTIVITY_EXPORT_FORMAT_KEY not in values:
            raise Exception("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        export_format = urllib.unquote_plus(values[Keys.ACTIVITY_EXPORT_FORMAT_KEY])
        if not export_format in ['csv', 'gpx', 'tcx']:
            raise Exception("Invalid format.")

        # Generate a random name for the local file.
        local_file_name = os.path.join(os.path.normpath(self.temp_dir), str(uuid.uuid4()))

        # Write the data to a temporary local file.
        exporter = Exporter.Exporter()
        exporter.export(self.data_mgr, activity_id, local_file_name, export_format)

        # Read the file into memory.
        result = ""
        try:
            with open(local_file_name, 'rb') as local_file:
                while True:
                    next_block = local_file.read(8192)
                    if not next_block:
                        break
                    result = result + next_block
        finally:
            # Remove the local file.
            os.remove(local_file_name)

        return True, result

    def handle_claim_device(self, values):
        """Called when an API message request to associate a device with the logged in user is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if 'device_id' not in values:
            raise Exception("Invalid parameter.")

        result = self.user_mgr.create_user_device_for_user_id(self.user_id, values['device_id'])
        return result, ""

    def handle_create_tag(self, values):
        """Called when an API message create a tag is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if Keys.ACTIVITY_TAG_KEY not in values:
            raise Exception("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        tag = urllib.unquote_plus(values[Keys.ACTIVITY_TAG_KEY])
        if not InputChecker.is_valid(tag):
            raise Exception("Invalid parameter.")

        result = self.data_mgr.create_tag(activity_id, tag)
        return result, ""

    def handle_delete_tag(self, values):
        """Called when an API message delete a tag is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if Keys.ACTIVITY_TAG_KEY not in values:
            raise Exception("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        tag = urllib.unquote_plus(values[Keys.ACTIVITY_TAG_KEY])
        if not InputChecker.is_valid(tag):
            raise Exception("Invalid parameter.")

        result = self.data_mgr.delete_tag(activity_id, tag)
        return result, ""

    def handle_list_tags(self, values):
        """Called when an API message create list tags associated with an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        result = self.data_mgr.retrieve_tags(activity_id)
        return result, ""

    def handle_create_comment(self, values):
        """Called when an API message create a comment is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if Keys.ACTIVITY_COMMENT_KEY not in values:
            raise Exception("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        comment = urllib.unquote_plus(values[Keys.ACTIVITY_COMMENT_KEY])
        if not InputChecker.is_valid(comment):
            raise Exception("Invalid parameter.")

        result = self.data_mgr.create_activity_comment(activity_id, self.user_id, comment)
        return result, ""

    def handle_list_comments(self, values):
        """Called when an API message create list comments associated with an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        result = self.data_mgr.retrieve_comments(activity_id)
        return result, ""

    def handle_update_settings(self, values):
        """Called when the user submits a setting change."""
        if self.user_id is None:
            raise Exception("Not logged in.")

        result = True

        # Update the user's setting.
        for key in values:
            decoded_key = urllib.unquote_plus(key)

            # Default privacy/visibility.
            if decoded_key == Keys.DEFAULT_PRIVACY:
                default_privacy = urllib.unquote_plus(values[key]).lower()
                if not (default_privacy == Keys.ACTIVITY_VISIBILITY_PUBLIC or default_privacy == Keys.ACTIVITY_VISIBILITY_PRIVATE):
                    raise Exception("Invalid visibility value.")
                result = self.user_mgr.update_user_setting(self.user_id, Keys.DEFAULT_PRIVACY, default_privacy)
            
            # Metric or imperial?
            elif decoded_key == Keys.PREFERRED_UNITS_KEY:
                preferred_units = urllib.unquote_plus(values[key]).lower()
                if not (preferred_units == Keys.UNITS_METRIC_KEY or preferred_units == Keys.UNITS_STANDARD_KEY):
                    raise Exception("Invalid units value.")
                result = self.user_mgr.update_user_setting(self.user_id, Keys.PREFERRED_UNITS_KEY, preferred_units)

        return result, ""

    def handle_update_profile(self, values):
        """Called when the user submits a profile change."""
        if self.user_id is None:
            raise Exception("Not logged in.")

        result = True

        # Update the user's profile.
        for key in values:
            decoded_key = urllib.unquote_plus(key)

            # Gender
            if decoded_key == Keys.HEIGHT_KEY:
                height = urllib.unquote_plus(values[key]).lower()
            elif decoded_key == Keys.WEIGHT_KEY:
                weight = urllib.unquote_plus(values[key]).lower()
            elif decoded_key == Keys.GENDER_KEY:
                gender = urllib.unquote_plus(values[key]).lower()
                if not (gender == Keys.GENDER_MALE_KEY or gender == Keys.GENDER_FEMALE_KEY):
                    raise Exception("Invalid gender value.")
                result = self.user_mgr.update_user_setting(self.user_id, Keys.GENDER_KEY, gender)

        return result, ""

    def handle_update_visibility(self, values):
        """Called when the user updates the visibility of an activity."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Drink ID not specified.")
        if Keys.ACTIVITY_VISIBILITY_KEY not in values:
            raise Exception("Visibility not specified.")

        visibility = urllib.unquote_plus(values[Keys.ACTIVITY_VISIBILITY_KEY])
        visibility = visibility.lower()
        if not (visibility == Keys.ACTIVITY_VISIBILITY_PUBLIC or visibility == Keys.ACTIVITY_VISIBILITY_PRIVATE):
            raise Exception("Invalid visibility value.")

        result = self.data_mgr.update_activity_visibility(values[Keys.ACTIVITY_ID_KEY], visibility)
        return result, ""

    def handle_refresh_analysis(self, values):
        """Called when the user wants to recalculate the summary data."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Drink ID not specified.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise Exception("Invalid activity ID.")

        activity = self.data_mgr.retrieve_activity(activity_id)
        if not activity:
            raise Exception("Invalid activity.")

        self.data_mgr.analyze(activity)
        return True, ""

    def handle_api_1_0_request(self, request, values):
        """Called to parse a version 1.0 API message."""
        username = None
        if self.user_id is None:
            if Keys.SESSION_KEY in values:
                username = self.user_mgr.get_logged_in_user_from_cookie(values[Keys.SESSION_KEY])
                if username is not None:
                    self.user_id, _, _ = self.user_mgr.retrieve_user(username)

        if request == 'update_status':
            return self.handle_update_status(values)
        elif request == 'login_submit':
            return self.handle_login_submit(values)
        elif request == 'create_login_submit':
            return self.handle_create_login_submit(values)
        elif request == 'login_status':
            return self.handle_login_status(values)
        elif request == 'logout':
            return self.handle_logout(values)
        elif request == 'update_email':
            return self.handle_update_email(values)
        elif request == 'update_password':
            return self.handle_update_password(values)
        elif request == 'delete_user':
            return self.handle_delete_user(values)
        elif request == 'list_activities':
            return self.handle_list_activities(values)
        elif request == 'delete_activity':
            return self.handle_delete_activity(values)
        elif request == 'add_activity':
            return self.handle_add_activity(values)
        elif request == 'upload_activity_file':
            return self.handle_upload_activity_file(username, values)
        elif request == 'add_tag_to_activity':
            return self.handle_add_tag_to_activity(values)
        elif request == 'delete_tag_from_activity':
            return self.handle_delete_tag_from_activity(values)
        elif request == 'list_matched_users':
            return self.handle_list_matched_users(values)
        elif request == 'list_users_following':
            return self.list_users_following(values)
        elif request == 'list_users_followed_by':
            return self.list_users_followed_by(values)
        elif request == 'request_to_follow':
            return self.handle_request_to_follow(values)
        elif request == 'unfollow':
            return self.handle_unfollow(values)
        elif request == 'export_activity':
            return self.handle_export_activity(values)
        elif request == 'claim_device':
            return self.handle_claim_device(values)
        elif request == 'create_tag':
            return self.handle_create_tag(values)
        elif request == 'delete_tag':
            return self.handle_delete_tag(values)
        elif request == 'list_tags':
            return self.handle_list_tags(values)
        elif request == 'create_comment':
            return self.handle_create_comment(values)
        elif request == 'list_comments':
            return self.handle_list_comments(values)
        elif request == 'update_settings':
            return self.handle_update_settings(values)
        elif request == 'update_profile':
            return self.handle_update_profile(values)
        elif request == 'update_visibility':
            return self.handle_update_visibility(values)
        elif request == 'refresh_analysis':
            return self.handle_refresh_analysis(values)
        return False, ""
