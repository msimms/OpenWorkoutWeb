# Copyright 2017 Michael J Simms
"""API request handlers"""

import json
import logging
import time
import urllib
import uuid
import Exporter
import InputChecker
import Keys

g_not_meta_data = ["DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy"]

class Api(object):
    """Class for managing API messages."""

    def __init__(self, user_mgr, data_mgr, analysis_scheduler, user_id):
        super(Api, self).__init__()
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.analysis_scheduler = analysis_scheduler
        self.user_id = user_id

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
            self.data_mgr.create_locations(device_str, activity_id, locations)

        if Keys.APP_ACCELEROMETER_KEY in values:

            # Parse each of the accelerometer objects.
            encoded_accel = values[Keys.APP_ACCELEROMETER_KEY]
            for accel_obj in encoded_accel:
                accel = self.parse_json_accel_obj(activity_id, accel_obj)
                accels.append(accel)

            # Update the accelerometer readings.
            self.data_mgr.create_accelerometer_reading(device_str, activity_id, accels)

        # Udpate the activity type.
        if len(activity_type) > 0:
            self.data_mgr.create_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, activity_type, False)

        # Update the user device association.
        if len(username) > 0:
            user_id, _, _ = self.user_mgr.retrieve_user(username)
            user_devices = self.user_mgr.retrieve_user_devices(user_id)
            if user_devices is not None and device_str not in user_devices:
                self.user_mgr.create_user_device(user_id, device_str)

        # Schedule for analysis.
        self.analysis_scheduler.add_to_queue(activity_id)

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
        password = values[Keys.PASSWORD_KEY]
        if not self.user_mgr.authenticate_user(username, password):
            raise Exception("Authentication failed.")

        # Delete all the user's activities.
        self.data_mgr.delete_user_activities(self.user_id)

        # Delete the user.
        self.user_mgr.delete_user(self.user_id)
        return True, ""

    def handle_delete_activity(self, values):
        """Removes the specified activity."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Activity ID not specified.")

        # Get the device and activity IDs from the push request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]

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
        if Keys.APP_TIME_KEY not in values:
            raise Exception("Time not specified.")
        if Keys.APP_DISTANCE_KEY not in values:
            raise Exception("Distance not specified.")

        activity_id = self.data_mgr.create_activity_id()
        return True, ""

    def handle_add_sets_and_reps_activity(self, values):
        """Called when an API message to add a new activity based on sets and reps is received."""
        if Keys.APP_SETS_KEY not in values:
            raise Exception("Sets not specified.")

        activity_id = self.data_mgr.create_activity_id()
        sets = values[Keys.APP_SETS_KEY]
        print sets
        return True, ""

    def handle_add_activity(self, values):
        """Called when an API message to add a new activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise Exception("Activity type not specified.")

        switcher = {
            Keys.TYPE_RUNNING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_CYCLING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_SWIMMING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_PULL_UPS_KEY : self.handle_add_sets_and_reps_activity
        }

        func = switcher.get(values[Keys.ACTIVITY_TYPE_KEY], lambda: "Invalid activity type")
        return True, func(values)

    def handle_upload_activity_file(self, values):
        """Called when an API message to upload a file is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.UPLOADED_FILE_NAME_KEY not in values:
            raise Exception("File name not specified.")
        if Keys.UPLOADED_FILE_DATA_KEY not in values:
            raise Exception("File data not specified.")

        # Generate a random name for the local file.
        uploaded_file_name = values[Keys.UPLOADED_FILE_NAME_KEY]
        upload_path = os.path.normpath(self.tempfile_dir)
        uploaded_file_name, uploaded_file_ext = os.path.splitext(uploaded_file_name)
        local_file_name = os.path.join(upload_path, str(uuid.uuid4()))
        local_file_name = local_file_name + uploaded_file_ext

        # Write the file.
        with open(local_file_name, 'wb') as local_file:
            local_file.write(values[Keys.UPLOADED_FILE_DATA_KEY])

        # Parse the file and store it's contents in the database.
        success, device_id, activity_id = self.data_mgr.import_file(username, self.user_id, local_file_name, uploaded_file_ext)
        if not success:
            raise Exception('Unhandled exception in upload when processing ' + uploaded_file_name)

        # Schedule for analysis.
        self.analysis_scheduler.add_to_queue(activity_id)

        # Remove the local file.
        os.remove(local_file_name)

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
        if Keys.TARGET_EMAIL_KEY not in values:
            raise Exception("Invalid parameter.")

        target_email = urllib.unquote_plus(values[Keys.TARGET_EMAIL_KEY])
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise Exception("Target user does not exist.")

        users_following = self.user_mgr.list_users_followed(self.user_id)
        users_list_str = ""
        if users_following is not None and isinstance(users_following, list):
            users_list_str = str(users_following)
        return True, users_list_str

    def list_users_followed_by(self, values):
        """Called when an API message to list the users who are following you is received."""
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

        exporter = Exporter.Exporter()
        result = exporter.export(self.data_mgr, values[Keys.ACTIVITY_ID_KEY])
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
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if Keys.ACTIVITY_TAGS_KEY not in values:
            raise Exception("Invalid parameter.")

        tags = values[Keys.ACTIVITY_TAGS_KEY]
        if not InputChecker.is_valid(tags):
            raise Exception("Invalid parameter.")

        result = self.data_mgr.create_tag(values[Keys.ACTIVITY_ID_KEY], tags)
        return result, ""

    def handle_list_tags(self, values):
        """Called when an API message create list tags associated with an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")

        result = self.data_mgr.retrieve_tags(values[Keys.ACTIVITY_ID_KEY])
        return result, ""

    def handle_create_comment(self, values):
        """Called when an API message create a comment is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")
        if Keys.ACTIVITY_COMMENT_KEY not in values:
            raise Exception("Invalid parameter.")

        comment = values[Keys.ACTIVITY_COMMENT_KEY]
        if not InputChecker.is_valid(comment):
            raise Exception("Invalid parameter.")

        result = self.data_mgr.create_activity_comment(values[Keys.ACTIVITY_ID_KEY], self.user_id, comment)
        return result, ""

    def handle_list_comments(self, values):
        """Called when an API message create list comments associated with an activity is received."""
        if self.user_id is None:
            raise Exception("Not logged in.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise Exception("Invalid parameter.")

        result = self.data_mgr.retrieve_comments(values[Keys.ACTIVITY_ID_KEY])
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

    def handle_api_1_0_request(self, request, values):
        """Called to parse a version 1.0 API message."""
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
        elif request == 'logout':
            return self.handle_logout(values)
        elif request == 'update_email':
            return self.handle_update_email(values)
        elif request == 'update_password':
            return self.handle_update_password(values)
        elif request == 'delete_user':
            return self.handle_delete_user(values)
        elif request == 'delete_activity':
            return self.handle_delete_activity(values)
        elif request == 'add_activity':
            return self.handle_add_activity(values)
        elif request == 'upload_activity_file':
            return self.handle_upload_activity_file(values)
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
        return False, ""
