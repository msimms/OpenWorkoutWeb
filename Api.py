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
"""API request handlers"""

import calendar
import datetime
import json
import logging
import sys
import time
import ApiException
import Exporter
import InputChecker
import Keys
import Units
import TrainingPaceCalculator

if sys.version_info[0] < 3:
    from urllib import unquote_plus
else:
    from urllib.parse import unquote_plus

class Api(object):
    """Class for managing API messages."""

    def __init__(self, user_mgr, data_mgr, user_id, root_url):
        super(Api, self).__init__()
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.user_id = user_id
        self.root_url = root_url

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.debug(log_str)

    def activity_belongs_to_logged_in_user(self, activity):
        """Returns True if the specified activity belongs to the logged in user."""
        if self.user_id is None:
            return False
        activity_user_id, _, _ = self.user_mgr.get_activity_user(activity)
        belongs_to_current_user = str(activity_user_id) == str(self.user_id)
        return belongs_to_current_user

    def activity_can_be_viewed(self, activity):
        """Determine if the requesting user can view the activity."""
        if self.user_id is None:
            return self.data_mgr.is_activity_public(activity)
        activity_user_id, _, _ = self.user_mgr.get_activity_user(activity)
        belongs_to_current_user = belongs_to_current_user = str(activity_user_id) == str(self.user_id)
        return self.data_mgr.is_activity_public(activity) or belongs_to_current_user

    def activity_id_can_be_viewed(self, activity_id):
        """Determine if the requesting user can view the activity."""
        if self.user_id is None:
            return self.data_mgr.is_activity_id_public(activity_id)
        activity_user_id, _, _ = self.user_mgr.get_activity_id_user(activity_id)
        belongs_to_current_user = belongs_to_current_user = str(activity_user_id) == str(self.user_id)
        return self.data_mgr.is_activity_id_public(activity_id) or belongs_to_current_user

    def parse_json_loc_obj(self, json_obj, sensor_readings_dict, metadata_list_dict):
        """Helper function that parses the JSON object, which contains location data, and updates the database."""
        location = []

        try:
            # Parse the metadata for the timestamp.
            if Keys.APP_TIME_KEY in json_obj:
                time_str = json_obj[Keys.APP_TIME_KEY]
                date_time = int(time_str)
            else:
                date_time = int(time.time() * 1000)

            # Parse the location data.
            try:
                lat = json_obj[Keys.APP_LOCATION_LAT_KEY]
                lon = json_obj[Keys.APP_LOCATION_LON_KEY]
                alt = json_obj[Keys.APP_LOCATION_ALT_KEY]
                horizontal_accuracy = json_obj[Keys.APP_HORIZONTAL_ACCURACY_KEY]
                vertical_accuracy = json_obj[Keys.APP_VERTICAL_ACCURACY_KEY]
                location = [date_time, lat, lon, alt, horizontal_accuracy, vertical_accuracy]
            except ValueError as e:
                self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
            except KeyError as e:
                self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
            except:
                self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))

            # Parse the rest of the data, which will be a combination of metadata and sensor data.
            for item in json_obj.iteritems():
                key = item[0]
                time_value_pair = []
                time_value_pair.append(date_time)
                time_value_pair.append(float(item[1]))
                if key in [Keys.APP_CADENCE_KEY, Keys.APP_HEART_RATE_KEY, Keys.APP_POWER_KEY]:
                    if key not in sensor_readings_dict:
                        sensor_readings_dict[key] = []
                    value_list = sensor_readings_dict[key]
                    value_list.append(time_value_pair)
                elif key in [Keys.APP_CURRENT_SPEED_KEY, Keys.APP_CURRENT_PACE_KEY]:
                    if key not in metadata_list_dict:
                        metadata_list_dict[key] = []
                    value_list = metadata_list_dict[key]
                    value_list.append(time_value_pair)
        except ValueError as e:
            self.log_error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except KeyError as e:
            self.log_error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except:
            self.log_error("Error parsing JSON location data. JSON object = " + str(json_obj))
        return location

    def parse_json_accel_obj(self, json_obj):
        """Helper function that parses the JSON object, which contains accelerometer data, and updates the database."""
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
        except ValueError as e:
            self.log_error("ValueError in JSON accelerometer data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except KeyError as e:
            self.log_error("KeyError in JSON accelerometer data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except:
            self.log_error("Error parsing JSON accelerometer data. JSON object = " + str(json_obj))
        return accel

    def handle_update_status(self, values):
        """Called when an API message to update the status of a device is received."""
        device_str = ""
        activity_id = ""
        activity_type = ""
        username = ""
        locations = []
        sensor_readings_dict = {}
        metadata_list_dict = {}

        # Parse required identifiers.
        device_str = values[Keys.APP_DEVICE_ID_KEY]
        activity_id = values[Keys.APP_ID_KEY]

        # Parse optional identifiers.
        if Keys.APP_TYPE_KEY in values:
            activity_type = values[Keys.APP_TYPE_KEY]
        if Keys.APP_USERNAME_KEY in values:
            username = values[Keys.APP_USERNAME_KEY]

        if Keys.APP_LOCATIONS_KEY in values:

            # Parse each of the location objects. Check for invalid data.
            encoded_locations = values[Keys.APP_LOCATIONS_KEY]
            for location_obj in encoded_locations:
                location = self.parse_json_loc_obj(location_obj, sensor_readings_dict, metadata_list_dict)

                # Ignore invalid readings. Invalid lat/lon are indicated as -1, but extremely high values should be ignored too. Units are meters.
                if InputChecker.is_valid_location(location[1], location[2], location[4]):
                    locations.append(location)

            # Update the activity.
            self.data_mgr.update_moving_activity(device_str, activity_id, locations, sensor_readings_dict, metadata_list_dict)

        if Keys.APP_ACCELEROMETER_KEY in values:

            # Parse each of the accelerometer objects.
            accels = []
            encoded_accel = values[Keys.APP_ACCELEROMETER_KEY]
            for accel_obj in encoded_accel:
                accel = self.parse_json_accel_obj(accel_obj)
                accels.append(accel)

            # Update the accelerometer readings.
            if accels:
                self.data_mgr.create_activity_accelerometer_reading(device_str, activity_id, accels)

        # Update the activity type.
        activity_type_updated = False
        if len(activity_type) > 0:

            # If the activity type was updated then set the default gear (will be done later after user id validation).
            activity_type_updated = self.data_mgr.create_activity_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, activity_type, False)

        # Valid user?
        if len(username) > 0:
            temp_user_id, _, _ = self.user_mgr.retrieve_user(username)
            if temp_user_id == self.user_id:

                # Update the user device association.
                user_devices = self.user_mgr.retrieve_user_devices(self.user_id)
                if user_devices is not None and device_str not in user_devices:
                    self.user_mgr.create_user_device_for_user_id(self.user_id, device_str)

                # Set the default gear.
                if activity_type_updated:
                    self.data_mgr.create_default_tags_on_activity(self.user_id, activity_type, activity_id)

        # Analysis is now obsolete, so delete it.
        self.data_mgr.delete_activity_summary(activity_id)

        return True, ""

    def handle_retrieve_activity_track(self, values):
        """Called when an API message to get the activity track is received. Result is a JSON string."""
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")
        if Keys.ACTIVITY_NUM_POINTS not in values:
            raise ApiException.ApiMalformedRequestException("Number of datapoints not specified.")

        # Get the device and activity IDs from the request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Validate the number of points to retrieve.
        num_points = values[Keys.ACTIVITY_NUM_POINTS]
        if not InputChecker.is_integer(num_points):
            raise ApiException.ApiMalformedRequestException("Invalid number of points.")
        num_points = int(num_points)

        # Get the activity from the database.
        activity = self.data_mgr.retrieve_activity(activity_id)

        # Determine if the requesting user can view the activity.
        if not self.activity_can_be_viewed(activity):
            return self.error("The requested activity is not viewable to this user.")

        response = "["

        if Keys.APP_LOCATIONS_KEY in activity:

            locations = activity[Keys.APP_LOCATIONS_KEY]
            for location in locations[num_points:]:
                if len(response) > 1:
                    response += ","
                if Keys.LOCATION_HORIZONTAL_ACCURACY_KEY in location and Keys.LOCATION_VERTICAL_ACCURACY_KEY in location:
                    response += json.dumps({Keys.LOCATION_LAT_KEY: location[Keys.LOCATION_LAT_KEY], Keys.LOCATION_LON_KEY: location[Keys.LOCATION_LON_KEY], Keys.LOCATION_ALT_KEY: location[Keys.LOCATION_ALT_KEY], Keys.LOCATION_TIME_KEY: location[Keys.LOCATION_TIME_KEY], Keys.LOCATION_HORIZONTAL_ACCURACY_KEY: location[Keys.LOCATION_HORIZONTAL_ACCURACY_KEY], Keys.LOCATION_VERTICAL_ACCURACY_KEY: location[Keys.LOCATION_VERTICAL_ACCURACY_KEY]})
                else:
                    response += json.dumps({Keys.LOCATION_LAT_KEY: location[Keys.LOCATION_LAT_KEY], Keys.LOCATION_LON_KEY: location[Keys.LOCATION_LON_KEY], Keys.LOCATION_ALT_KEY: location[Keys.LOCATION_ALT_KEY], Keys.LOCATION_TIME_KEY: location[Keys.LOCATION_TIME_KEY]})

        response += "]"

        return True, response

    def handle_retrieve_activity_metadata(self, values):
        """Called when an API message to get the activity metadata. Result is a JSON string."""
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")

        # Get the activity ID from the request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Get the activity from the database.
        activity = self.data_mgr.retrieve_activity(activity_id)

        # Determine if the requesting user can view the activity.
        if not self.activity_can_be_viewed(activity):
            return self.error("The requested activity is not viewable to this user.")

        # Is this is a foot based activity? Need to know so we can display steps per minute instead of revs per minute.
        is_foot_based = False

        # Need to know which version of python we're working with.
        py_version = sys.version_info[0]

        response_dict = {}
        response_dict[Keys.ACTIVITY_ID_KEY] = activity_id

        if Keys.ACTIVITY_NAME_KEY in activity:
            activity_name = activity[Keys.ACTIVITY_NAME_KEY]
            if activity_name is not None and len(activity_name) > 0:
                response_dict["Name"] = activity_name

        if Keys.ACTIVITY_TYPE_KEY in activity:
            activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
            if activity_type is not None and len(activity_type) > 0:
                is_foot_based = activity_type in Keys.FOOT_BASED_ACTIVITIES
                response_dict["Type"] = activity_type

        if Keys.ACTIVITY_DESCRIPTION_KEY in activity:
            activity_description = activity[Keys.ACTIVITY_DESCRIPTION_KEY]
            if activity_description is not None and len(activity_description) > 0:
                response_dict["Description"] = activity_description

        if Keys.ACTIVITY_START_TIME_KEY in activity:
            activity_time = activity[Keys.ACTIVITY_START_TIME_KEY]
            if activity_time is not None:
                response_dict["Time"] = activity_time

        if Keys.APP_DISTANCE_KEY in activity:
            distances = activity[Keys.APP_DISTANCE_KEY]
            if distances is not None and len(distances) > 0:
                distance = distances[-1]
                if py_version < 3:
                    value = float(distance.values()[0])
                else:
                    value = float(list(distance.values())[0])
                response_dict[Keys.APP_DISTANCE_KEY] = value

        if Keys.APP_AVG_SPEED_KEY in activity:
            avg_speeds = activity[Keys.APP_AVG_SPEED_KEY]
            if avg_speeds is not None and len(avg_speeds) > 0:
                speed = avg_speeds[-1]
                if py_version < 3:
                    value = float(speed.values()[0])
                else:
                    value = float(list(speed.values())[0])
                response_dict[Keys.APP_AVG_SPEED_KEY] = value

        if Keys.APP_MOVING_SPEED_KEY in activity:
            moving_speeds = activity[Keys.APP_MOVING_SPEED_KEY]
            if moving_speeds is not None and len(moving_speeds) > 0:
                speed = moving_speeds[-1]
                if py_version < 3:
                    value = float(speed.values()[0])
                else:
                    value = float(list(speed.values())[0])
                response_dict[Keys.APP_MOVING_SPEED_KEY] = value

        if Keys.APP_HEART_RATE_KEY in activity:
            heart_rates = activity[Keys.APP_HEART_RATE_KEY]
            if heart_rates is not None and len(heart_rates) > 0:
                heart_rate = heart_rates[-1]
                if py_version < 3:
                    value = float(heart_rate.values()[0])
                else:
                    value = float(list(heart_rate.values())[0])
                response_dict[Keys.APP_HEART_RATE_KEY] = value

        if Keys.APP_CADENCE_KEY in activity:
            cadences = activity[Keys.APP_CADENCE_KEY]
            if cadences is not None and len(cadences) > 0:
                cadence = cadences[-1]
                if py_version < 3:
                    value = float(cadence.values()[0])
                else:
                    value = float(list(cadence.values())[0])
                if is_foot_based:
                    value = value * 2.0
                response_dict[Keys.APP_CADENCE_KEY] = value

        if Keys.APP_POWER_KEY in activity:
            powers = activity[Keys.APP_POWER_KEY]
            if powers is not None and len(powers) > 0:
                power = powers[-1]
                if py_version < 3:
                    value = float(power.values()[0])
                else:
                    value = float(list(power.values())[0])
                response_dict[Keys.APP_POWER_KEY] = value

        response = json.dumps(response_dict)

        return True, response

    def handle_retrieve_activity_sensordata(self, values):
        """Called when an API message to get the activity sensordata. Result is a JSON string."""
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")
        if Keys.SENSOR_LIST_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Sensor list not specified.")

        # Get the activity ID from the request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Get the activity from the database.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if activity is None:
            raise ApiException.ApiMalformedRequestException("Invalid activity object.")

        # Determine if the requesting user can view the activity.
        if not self.activity_can_be_viewed(activity):
            return self.error("The requested activity is not viewable to this user.")

        response = {}

        for sensor_name in values[Keys.SENSOR_LIST_KEY].split(','):
            if sensor_name in activity:

                # Need to fix up the datetime item for each event.
                if sensor_name == 'Events':
                    events = activity[sensor_name]
                    for event in events:
                        if 'timestamp' in event:
                            dt_tuple = event['timestamp'].timetuple()
                            dt_unix = calendar.timegm(dt_tuple)
                            event['timestamp'] = dt_unix
                        if 'start_time' in event:
                            dt_tuple = event['start_time'].timetuple()
                            dt_unix = calendar.timegm(dt_tuple)
                            event['start_time'] = dt_unix
                        if 'local_timestamp' in event:
                            dt_tuple = event['local_timestamp'].timetuple()
                            dt_unix = calendar.timegm(dt_tuple)
                            event['local_timestamp'] = dt_unix
                    response[sensor_name] = events
                else:
                    response[sensor_name] = activity[sensor_name]

        return True, json.dumps(response)

    def handle_retrieve_activity_summarydata(self, values):
        """Called when an API message to get the interval segments computed from the activity is received. Result is a JSON string."""
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")
        if Keys.SUMMARY_ITEMS_LIST_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Summary item list not specified.")

        # Get the activity ID from the request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Determine if the requesting user can view the activity.
        if not self.activity_id_can_be_viewed(activity_id):
            return self.error("The requested activity is not viewable to this user.")

        # Get the activity summary from the database.
        activity_summary = self.data_mgr.retrieve_activity_summary(activity_id)

        response = {}

        for summary_item in values[Keys.SUMMARY_ITEMS_LIST_KEY].split(','):
            if summary_item in activity_summary:
                response[summary_item] = activity_summary[summary_item]

        return True, json.dumps(response)

    def handle_update_activity_metadata(self, values):
        """Called when an API message to update the activity metadata."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")

        # Get the activity ID from the request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Get the activity from the database.
        activity = self.data_mgr.retrieve_activity(activity_id)

        # Get the ID of the user that owns the activity and make sure it's the current user.
        if not self.activity_belongs_to_logged_in_user(activity):
            raise ApiException.ApiAuthenticationException("Not activity owner.")

        if Keys.ACTIVITY_NAME_KEY in values:
            if not self.data_mgr.create_activity_metadata(activity_id, 0, Keys.ACTIVITY_NAME_KEY, unquote_plus(values[Keys.ACTIVITY_NAME_KEY]), False):
                raise Exception("Failed to update activity name.")
        if Keys.ACTIVITY_TYPE_KEY in values:
            if not self.data_mgr.create_activity_metadata(activity_id, 0, Keys.ACTIVITY_TYPE_KEY, unquote_plus(values[Keys.ACTIVITY_TYPE_KEY]), False):
                raise Exception("Failed to update activity type.")
        if Keys.ACTIVITY_DESCRIPTION_KEY in values:
            if not self.data_mgr.create_activity_metadata(activity_id, 0, Keys.ACTIVITY_DESCRIPTION_KEY, unquote_plus(values[Keys.ACTIVITY_DESCRIPTION_KEY]), False):
                raise Exception("Failed to update activity description.")

        return True, ""

    def handle_login(self, values):
        """Called when an API message to log in is received."""
        if self.user_id is not None:
            return True, self.user_mgr.get_logged_in_user()

        if Keys.USERNAME_KEY not in values:
            raise ApiException.ApiAuthenticationException("Username not specified.")
        if Keys.PASSWORD_KEY not in values:
            raise ApiException.ApiAuthenticationException("Password not specified.")

        email = unquote_plus(values[Keys.USERNAME_KEY])
        if not InputChecker.is_email_address(email):
            raise ApiException.ApiAuthenticationException("Invalid email address.")
        password = unquote_plus(values[Keys.PASSWORD_KEY])

        try:
            if not self.user_mgr.authenticate_user(email, password):
                raise ApiException.ApiAuthenticationException("Authentication failed.")
        except Exception as e:
            raise ApiException.ApiAuthenticationException(str(e))

        if Keys.DEVICE_KEY in values:
            device_str = unquote_plus(values[Keys.DEVICE_KEY])
            result = self.user_mgr.create_user_device(email, device_str)
        else:
            result = True

        cookie = self.user_mgr.create_new_session(email)
        return result, str(cookie)

    def handle_create_login(self, values):
        """Called when an API message to create an account is received."""
        if self.user_id is not None:
            raise Exception("Already logged in.")

        if Keys.USERNAME_KEY not in values:
            raise ApiException.ApiAuthenticationException("Username not specified.")
        if Keys.REALNAME_KEY not in values:
            raise ApiException.ApiAuthenticationException("Real name not specified.")
        if Keys.PASSWORD1_KEY not in values:
            raise ApiException.ApiAuthenticationException("Password not specified.")
        if Keys.PASSWORD2_KEY not in values:
            raise ApiException.ApiAuthenticationException("Password confirmation not specified.")

        email = unquote_plus(values[Keys.USERNAME_KEY])
        if not InputChecker.is_email_address(email):
            raise ApiException.ApiMalformedRequestException("Invalid email address.")
        realname = unquote_plus(values[Keys.REALNAME_KEY])
        if not InputChecker.is_valid_decoded_str(realname):
            raise ApiException.ApiMalformedRequestException("Invalid name.")
        password1 = unquote_plus(values[Keys.PASSWORD1_KEY])
        password2 = unquote_plus(values[Keys.PASSWORD2_KEY])

        if Keys.DEVICE_KEY in values:
            device_str = unquote_plus(values[Keys.DEVICE_KEY])
        else:
            device_str = ""

        try:
            if not self.user_mgr.create_user(email, realname, password1, password2, device_str):
                raise Exception("User creation failed.")
        except:
            raise Exception("User creation failed.")

        cookie = self.user_mgr.create_new_session(email)
        return True, str(cookie)

    def handle_login_status(self, values):
        """Called when an API message to check the login status in is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        return True, "Logged In"

    def handle_logout(self, values):
        """Ends the session for the specified user."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        # End the session
        self.user_mgr.clear_current_session()
        self.user_id = None
        return True, "Logged Out"

    def handle_update_email(self, values):
        """Updates the user's email address."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.EMAIL_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Email not specified.")

        # Get the logged in user.
        current_username = self.user_mgr.get_logged_in_user()
        if current_username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Decode the parameter.
        new_username = unquote_plus(values[Keys.EMAIL_KEY])

        # Get the user details.
        user_id, _, user_realname = self.user_mgr.retrieve_user(current_username)

        # Update the user's password in the database.
        if not self.user_mgr.update_user_email(user_id, new_username, user_realname):
            raise Exception("Update failed.")
        return True, ""

    def handle_update_password(self, values):
        """Updates the user's password."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if 'old_password' not in values:
            raise ApiException.ApiMalformedRequestException("Old password not specified.")
        if 'new_password1' not in values:
            raise ApiException.ApiMalformedRequestException("New password not specified.")
        if 'new_password2' not in values:
            raise ApiException.ApiMalformedRequestException("New password confirmation not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Get the user details.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)

        # The the old and new passwords from the request.
        old_password = unquote_plus(values["old_password"])
        new_password1 = unquote_plus(values["new_password1"])
        new_password2 = unquote_plus(values["new_password2"])

        # Reauthenticate the user.
        if not self.user_mgr.authenticate_user(username, old_password):
            raise Exception("Authentication failed.")

        # Update the user's password in the database.
        if not self.user_mgr.update_user_password(user_id, username, user_realname, new_password1, new_password2):
            raise Exception("Update failed.")
        return True, ""

    def handle_delete_users_gear(self, values):
        """Removes the current user's gear data."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.PASSWORD_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Password not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Reauthenticate the user.
        password = unquote_plus(values[Keys.PASSWORD_KEY])
        if not self.user_mgr.authenticate_user(username, password):
            raise Exception("Authentication failed.")

        # Delete all the user's gear.
        self.data_mgr.delete_user_gear(self.user_id)
        return True, ""

    def handle_delete_users_activities(self, values):
        """Removes the current user's activity data."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.PASSWORD_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Password not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Reauthenticate the user.
        password = unquote_plus(values[Keys.PASSWORD_KEY])
        if not self.user_mgr.authenticate_user(username, password):
            raise Exception("Authentication failed.")

        # Delete all the user's activities.
        self.data_mgr.delete_user_activities(self.user_id)

        # Delete the cache of the user's personal records.
        self.data_mgr.delete_all_user_personal_records(self.user_id)

        return True, ""

    def handle_delete_user(self, values):
        """Removes the current user and all associated data."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.PASSWORD_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Password not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Reauthenticate the user.
        password = unquote_plus(values[Keys.PASSWORD_KEY])
        if not self.user_mgr.authenticate_user(username, password):
            raise Exception("Authentication failed.")

        # Delete all of the user's activities.
        self.data_mgr.delete_user_activities(self.user_id)

        # Delete the user.
        self.user_mgr.delete_user(self.user_id)
        return True, ""

    def handle_list_devices(self, values):
        """Returns a JSON string describing all of the user's devices."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # List the devices.
        user_device_ids = self.user_mgr.retrieve_user_devices(self.user_id)

        # Get the time each device was last heard from.
        devices = []
        for device_id in user_device_ids:
            device_info = {}
            device_info[Keys.APP_DEVICE_ID_KEY] = device_id
            activity = self.data_mgr.retrieve_most_recent_activity_for_device(device_id)
            if activity is not None:
                device_info[Keys.DEVICE_LAST_HEARD_FROM] = activity[Keys.ACTIVITY_START_TIME_KEY]
            else:
                device_info[Keys.DEVICE_LAST_HEARD_FROM] = 0
            devices.append(device_info)

        json_result = json.dumps(devices, ensure_ascii=False)
        return True, json_result

    def handle_list_activities(self, values, include_friends):
        """Returns a JSON string describing all of the user's activities."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        # Fetch and validate the activity start and end times (optional).
        start_time = None
        end_time = None
        if Keys.START_DATE_KEY in values:
            start_time = int(datetime.datetime.strptime(values[Keys.START_DATE_KEY], '%Y-%m-%d').strftime("%s"))
        if Keys.END_DATE_KEY in values:
            end_time = int(datetime.datetime.strptime(values[Keys.END_DATE_KEY], '%Y-%m-%d').strftime("%s"))
        if Keys.START_TIME_KEY in values:
            start_time = values[Keys.START_TIME_KEY]
            if InputChecker.is_integer(start_time):
                start_time = int(start_time)
            else:
                raise ApiException.ApiMalformedRequestException("Invalid start time.")
        if Keys.END_TIME_KEY in values:
            end_time = values[Keys.END_TIME_KEY]
            if InputChecker.is_integer(end_time):
                end_time = int(end_time)
            else:
                raise ApiException.ApiMalformedRequestException("Invalid end time.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Get the user details.
        _, _, user_realname = self.user_mgr.retrieve_user(username)

        # Get the activities that belong to the logged in user.
        matched_activities = []
        if include_friends:
            activities = self.data_mgr.retrieve_all_activities_visible_to_user(self.user_id, user_realname, start_time, end_time, None)
        else:
            activities = self.data_mgr.retrieve_user_activity_list(self.user_id, user_realname, start_time, end_time, None)

        # Convert the activities list to an array of JSON objects for return to the client.
        if activities is not None and isinstance(activities, list):
            for activity in activities:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY
                activity_name = Keys.UNNAMED_ACTIVITY_TITLE
                if Keys.ACTIVITY_TYPE_KEY in activity:
                    activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
                if Keys.ACTIVITY_NAME_KEY in activity:
                    activity_name = activity[Keys.ACTIVITY_NAME_KEY]

                if Keys.ACTIVITY_START_TIME_KEY in activity and Keys.ACTIVITY_ID_KEY in activity:
                    url = self.root_url + "/activity/" + activity[Keys.ACTIVITY_ID_KEY]
                    temp_activity = {'title':'[' + activity_type + '] ' + activity_name, 'url':url, 'time': int(activity[Keys.ACTIVITY_START_TIME_KEY])}
                matched_activities.append(temp_activity)

        json_result = json.dumps(matched_activities, ensure_ascii=False)
        return True, json_result

    def handle_delete_activity(self, values):
        """Removes the specified activity."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")

        # Get the device and activity IDs from the request.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Only the activity's owner should be able to do this.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if not self.activity_belongs_to_logged_in_user(activity):
            raise ApiException.ApiAuthenticationException("Not activity owner.")

        # Delete the activity.
        deleted = self.data_mgr.delete_activity(self.user_id, activity_id)

        # Did we find it?
        if not deleted:
            raise Exception("An error occurred. Nothing was deleted.")

        return True, ""

    def handle_add_time_and_distance_activity(self, values):
        """Called when an API message to add a new activity based on time and distance is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.APP_DISTANCE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Distance not specified.")
        if Keys.APP_DURATION_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Duration not specified.")
        if Keys.ACTIVITY_START_TIME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity start time not specified.")
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity type not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Validate the activity start time.
        start_time = values[Keys.ACTIVITY_START_TIME_KEY]
        if not InputChecker.is_integer(start_time):
            raise ApiException.ApiMalformedRequestException("Invalid start time.")

        # Add the activity to the database.
        activity_type = values[Keys.ACTIVITY_TYPE_KEY]
        if not InputChecker.is_valid_decoded_str(activity_type):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        _, activity_id = self.data_mgr.create_activity(username, self.user_id, "", "", activity_type, int(start_time), None)

        # Add the activity data to the database.
        self.data_mgr.create_activity_metadata(activity_id, 0, Keys.APP_DISTANCE_KEY, float(values[Keys.APP_DISTANCE_KEY]), False)
        self.data_mgr.create_activity_metadata(activity_id, 0, Keys.APP_DURATION_KEY, float(values[Keys.APP_DURATION_KEY]), False)

        return ""

    def handle_add_sets_and_reps_activity(self, values):
        """Called when an API message to add a new activity based on sets and reps is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.APP_SETS_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Sets not specified.")
        if Keys.ACTIVITY_START_TIME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity start time not specified.")
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity type not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Convert the array string to an actual array (note: I realize I could use eval for this, but that seems dangerous)
        sets = unquote_plus(values[Keys.APP_SETS_KEY])
        if len(sets) <= 2:
            raise ApiException.ApiMalformedRequestException("Malformed set data.")
        sets = sets[1:-1] # Remove the brackets
        sets = sets.split(',')
        if len(sets) == 0:
            raise ApiException.ApiMalformedRequestException("Set data was not specified.")

        # Make sure everything is a number.
        new_sets = []
        for current_set in sets:
            rep_count = int(current_set)
            if rep_count > 0:
                new_sets.append(rep_count)

        # Make sure we got at least one valid set.
        if len(new_sets) == 0:
            raise ApiException.ApiMalformedRequestException("Set data was not specified.")

        # Validate the activity start time.
        start_time = values[Keys.ACTIVITY_START_TIME_KEY]
        if not InputChecker.is_integer(start_time):
            raise ApiException.ApiMalformedRequestException("Invalid start time.")

        # Validate the activity type.
        activity_type = values[Keys.ACTIVITY_TYPE_KEY]
        if not InputChecker.is_valid_decoded_str(activity_type):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Add the activity to the database.
        _, activity_id = self.data_mgr.create_activity(username, self.user_id, "", "", activity_type, int(start_time), None)
        self.data_mgr.create_activity_sets_and_reps_data(activity_id, new_sets)

        return ""

    def handle_add_activity(self, values):
        """Called when an API message to add a new activity is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity type not specified.")

        activity_type = values[Keys.ACTIVITY_TYPE_KEY]
        switcher = {
            Keys.TYPE_RUNNING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_CYCLING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_OPEN_WATER_SWIMMING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_POOL_SWIMMING_KEY : self.handle_add_time_and_distance_activity,
            Keys.TYPE_PULL_UP_KEY : self.handle_add_sets_and_reps_activity,
            Keys.TYPE_PUSH_UP_KEY : self.handle_add_sets_and_reps_activity
        }

        func = switcher.get(activity_type, lambda: "Invalid activity type")
        return True, func(values)

    def handle_upload_activity_file(self, values):
        """Called when an API message to create a new activity from data within a file is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.UPLOADED_FILE_NAME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("File name not specified.")
        if Keys.UPLOADED_FILE_DATA_KEY not in values:
            raise ApiException.ApiMalformedRequestException("File data not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiNotLoggedInException()

        # Decode the parameters.
        uploaded_file_name = unquote_plus(values[Keys.UPLOADED_FILE_NAME_KEY])
        uploaded_file_data = unquote_plus(values[Keys.UPLOADED_FILE_DATA_KEY])

        # Check for empty.
        if len(uploaded_file_name) == 0:
            raise ApiException.ApiMalformedRequestException('Empty file name.')
        if len(uploaded_file_data) == 0:
            raise ApiException.ApiMalformedRequestException('Empty file data for ' + uploaded_file_name + '.')

        # Validate the activity ID.
        desired_activity_id = None
        if Keys.ACTIVITY_ID_KEY in values:
            desired_activity_id = values[Keys.ACTIVITY_ID_KEY]
            if not InputChecker.is_uuid(desired_activity_id):
                raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Parse the file and store it's contents in the database.
        task_id = self.data_mgr.import_activity_from_file(username, self.user_id, uploaded_file_data, uploaded_file_name, desired_activity_id)

        return True, str(task_id)

    def handle_upload_activity_photo(self, values):
        """Called when an API message to upload a photo to an activity is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.UPLOADED_FILE_DATA_KEY not in values:
            raise ApiException.ApiMalformedRequestException("File data not specified.")
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiNotLoggedInException()

        # Is the user allowed to upload photos?
        can_upload = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_CAN_UPLOAD_PHOTOS_KEY)
        if not can_upload:
            raise ApiException.ApiAuthenticationException("User is not authorized to upload photos.")

        # Decode the parameters.
        uploaded_file_data = unquote_plus(values[Keys.UPLOADED_FILE_DATA_KEY])

        # Check for empty.
        if len(uploaded_file_data) == 0:
            raise ApiException.ApiMalformedRequestException('Empty file data.')

        # Validate the activity ID.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Only the activity's owner should be able to do this.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if not self.activity_belongs_to_logged_in_user(activity):
            raise ApiException.ApiAuthenticationException("Not activity owner.")

        # Parse the file and store it's contents in the database.
        try:
            result = self.data_mgr.attach_photo_to_activity(self.user_id, uploaded_file_data, activity_id)
        except Exception as e:
            raise ApiException.ApiMalformedRequestException(str(e))

        return result, ""

    def handle_list_activity_photos(self, values):
        """Lists all photos associated with an activity."""
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Validate the activity ID.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # List the IDs of each photo attached to this activity.
        result = {}
        result["photo ids"] = self.data_mgr.list_activity_photos(activity_id)

        json_result = json.dumps(result, ensure_ascii=False)
        return True, json_result

    def handle_delete_activity_photo(self, values):
        """Called when an API message to delete a photo and remove it from an activity is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.ACTIVITY_PHOTO_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiNotLoggedInException()

        # Validate the activity ID.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Validate the photo ID.
        photo_id = values[Keys.ACTIVITY_PHOTO_ID_KEY]
        if not InputChecker.is_hex_str(photo_id):
            raise ApiException.ApiMalformedRequestException("Invalid photo ID.")

        # Only the activity's owner should be able to do this.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if not self.activity_belongs_to_logged_in_user(activity):
            raise ApiException.ApiAuthenticationException("Not activity owner.")

        # Delete the photo.
        result = self.data_mgr.delete_activity_photo(activity_id, photo_id)

        return result, ""

    def handle_create_tags_on_activity(self, values):
        """Called when an API message to add a tag to an activity is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Validate the activity ID.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        tags = []
        tag_index = 0
        tag_name = Keys.ACTIVITY_TAG_KEY + str(tag_index)
        while tag_name in values:
            tag = unquote_plus(values[tag_name])
            if not InputChecker.is_valid_decoded_str(tag):
                raise ApiException.ApiMalformedRequestException("Invalid parameter.")
            tags.append(tag)
            tag_index = tag_index + 1
            tag_name = Keys.ACTIVITY_TAG_KEY + str(tag_index)

        # Only the activity's owner should be able to do this.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if not self.activity_belongs_to_logged_in_user(activity):
            raise ApiException.ApiAuthenticationException("Not activity owner.")

        result = self.data_mgr.create_tags_on_activity(activity, tags)
        return result, ""

    def handle_delete_tag_from_activity(self, values):
        """Called when an API message to delete a tag from an activity is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        # Validate the activity ID.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        return True, ""

    def handle_list_matched_users(self, values):
        """Called when an API message to list users is received. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if 'searchname' not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        search_name = unquote_plus(values['searchname'])
        search_name_len = len(search_name)
        if search_name_len < 3:
            raise ApiException.ApiMalformedRequestException("Search name is too short.")
        if search_name_len > 100:
            raise ApiException.ApiMalformedRequestException("Search name is too long.")

        matched_users = self.user_mgr.retrieve_matched_users(search_name)[:100] # Limit the number of results
        json_result = json.dumps(matched_users, ensure_ascii=False)
        return True, json_result

    def list_pending_friends(self, values):
        """Called when an API message to list the users requesting friendship with the current user is received. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        friends = self.user_mgr.list_pending_friends(self.user_id)
        json_result = json.dumps(friends, ensure_ascii=False)
        return True, json_result

    def list_friends(self, values):
        """Called when an API message to list the current user's friends is received. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        friends = self.user_mgr.list_friends(self.user_id)
        json_result = json.dumps(friends, ensure_ascii=False)
        return True, json_result

    def handle_friend_request(self, values):
        """Called when an API message request to friend another user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.TARGET_EMAIL_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        target_email = unquote_plus(values[Keys.TARGET_EMAIL_KEY])
        if not InputChecker.is_email_address(target_email):
            raise ApiException.ApiMalformedRequestException("Invalid email address.")
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise ApiException.ApiMalformedRequestException("Target user does not exist.")

        if not self.user_mgr.request_to_be_friends(self.user_id, target_id):
            raise ApiException.ApiMalformedRequestException("Request failed.")
        return True, ""

    def handle_confirm_friend_request(self, values):
        """Takes a user to the pending friends list and adds them to the actual friends list."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.TARGET_EMAIL_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        target_email = unquote_plus(values[Keys.TARGET_EMAIL_KEY])
        if not InputChecker.is_email_address(target_email):
            raise ApiException.ApiMalformedRequestException("Invalid email address.")
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise ApiException.ApiMalformedRequestException("Target user does not exist.")

        if not self.user_mgr.confirm_request_to_be_friends(self.user_id, target_id):
            raise ApiException.ApiMalformedRequestException("Request failed.")
        return True, ""

    def handle_unfriend_request(self, values):
        """Called when an API message request to unfriend another user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.TARGET_EMAIL_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        target_email = unquote_plus(values[Keys.TARGET_EMAIL_KEY])
        if not InputChecker.is_email_address(target_email):
            raise ApiException.ApiMalformedRequestException("Invalid email address.")
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            raise ApiException.ApiMalformedRequestException("Target user does not exist.")

        if not self.user_mgr.unfriend(self.user_id, target_id):
            raise ApiException.ApiMalformedRequestException("Request failed.")
        return True, ""

    def handle_export_activity(self, values):
        """Called when an API message request to export an activity is received."""
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Missing activity ID parameter.")
        if Keys.ACTIVITY_EXPORT_FORMAT_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Missing format parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        export_format = values[Keys.ACTIVITY_EXPORT_FORMAT_KEY]
        if not export_format in ['csv', 'gpx', 'tcx']:
            raise ApiException.ApiMalformedRequestException("Invalid format.")

        activity = self.data_mgr.retrieve_activity(activity_id)
        if not self.activity_can_be_viewed(activity):
            return self.error("The requested activity is not viewable to this user.")

        exporter = Exporter.Exporter()
        result = exporter.export(activity, None, export_format)

        return True, result

    def handle_export_workout(self, values):
        """Called when an API message request to export a workout description is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.WORKOUT_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Workout ID not specified.")
        if Keys.WORKOUT_FORMAT_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Export format not specified.")

        workout_id = values[Keys.WORKOUT_ID_KEY]
        if not InputChecker.is_uuid(workout_id):
            raise ApiException.ApiMalformedRequestException("Invalid workout ID.")
        export_format = values[Keys.WORKOUT_FORMAT_KEY]

        unit_system = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_PREFERRED_UNITS_KEY)

        # Get the workouts that belong to the logged in user.
        workout = self.data_mgr.retrieve_planned_workout(self.user_id, workout_id)
        result = ""
        if export_format == 'zwo':
            result = workout.export_to_zwo(workout_id)
        elif export_format == 'txt':
            result = workout.export_to_text(unit_system)
        elif export_format == 'json':
            result = workout.export_to_json_str(unit_system)
        elif export_format == 'ics':
            result = workout.export_to_ics(unit_system)
        return True, result

    def handle_claim_device(self, values):
        """Called when an API message request to associate a device with the logged in user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if 'device_id' not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.user_mgr.create_user_device_for_user_id(self.user_id, values['device_id'])
        return result, ""

    def handle_create_tag(self, values):
        """Called when an API message create a tag is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.ACTIVITY_TAG_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        tag = values[Keys.ACTIVITY_TAG_KEY]
        if not InputChecker.is_valid_decoded_str(tag):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if len(tag) == 0:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.create_activity_tag(activity_id, tag)
        return result, ""

    def handle_delete_tag(self, values):
        """Called when an API message delete a tag is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.ACTIVITY_TAG_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        tag = values[Keys.ACTIVITY_TAG_KEY]
        if not InputChecker.is_valid_decoded_str(tag):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.delete_tag(activity_id, tag)
        return result, ""

    def handle_list_tags(self, values):
        """Called when an API message create list tags associated with an activity is received. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        tags = self.data_mgr.retrieve_activity_tags(activity_id)
        json_result = json.dumps(tags, ensure_ascii=False)
        return True, json_result

    def handle_create_comment(self, values):
        """Called when an API message create a comment is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.ACTIVITY_COMMENT_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")
        comment = values[Keys.ACTIVITY_COMMENT_KEY]
        if not InputChecker.is_valid_decoded_str(comment):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.create_activity_comment(activity_id, self.user_id, comment)
        return result, ""

    def handle_list_comments(self, values):
        """Called when an API message to list comments associated with an activity is received. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        comments = self.data_mgr.retrieve_comments(activity_id)
        json_result = json.dumps(comments, ensure_ascii=False)
        return True, json_result

    def handle_create_gear(self, values):
        """Called when an API message to create gear for a user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.GEAR_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_NAME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_DESCRIPTION_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_ADD_TIME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        gear_type = values[Keys.GEAR_TYPE_KEY]
        if not InputChecker.is_valid_decoded_str(gear_type):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_name = values[Keys.GEAR_NAME_KEY]
        if not InputChecker.is_valid_decoded_str(gear_name):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_description = values[Keys.GEAR_DESCRIPTION_KEY]
        if not InputChecker.is_valid_decoded_str(gear_description):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_add_time = values[Keys.GEAR_ADD_TIME_KEY]
        if not InputChecker.is_integer(gear_add_time):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Retired date is optional.
        if Keys.GEAR_RETIRE_TIME_KEY in values and values[Keys.GEAR_RETIRE_TIME_KEY] is not None and len(values[Keys.GEAR_RETIRE_TIME_KEY]) > 0:
            gear_retire_time = values[Keys.GEAR_RETIRE_TIME_KEY]
            if gear_retire_time == 'NaN':
                gear_retire_time = 0
            elif not InputChecker.is_integer(gear_retire_time):
                raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        else:
            gear_retire_time = 0

        result = self.data_mgr.create_gear(self.user_id, gear_type, gear_name, gear_description, int(gear_add_time), int(gear_retire_time))
        return result, ""

    def handle_list_gear(self, values):
        """Called when an API message to list gear associated with a user is received. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        response = self.data_mgr.retrieve_gear(self.user_id)
        return True, json.dumps(response)

    def handle_list_gear_defaults(self, values):
        """Called when an API message to list the gear that is, by default, associated with each activity type. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        response = self.data_mgr.retrieve_gear_defaults(self.user_id)
        return True, json.dumps(response)

    def handle_update_gear(self, values):
        """Called when an API message to update gear for a user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.GEAR_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_NAME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_DESCRIPTION_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_ADD_TIME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        gear_id = values[Keys.GEAR_ID_KEY]
        if not InputChecker.is_uuid(gear_id):
            raise ApiException.ApiMalformedRequestException("Invalid gear ID.")
        gear_type = values[Keys.GEAR_TYPE_KEY]
        if not InputChecker.is_valid_decoded_str(gear_type):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_name = values[Keys.GEAR_NAME_KEY]
        if not InputChecker.is_valid_decoded_str(gear_name):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_description = values[Keys.GEAR_DESCRIPTION_KEY]
        if not InputChecker.is_valid_decoded_str(gear_description):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_add_time = values[Keys.GEAR_ADD_TIME_KEY]
        if not InputChecker.is_integer(gear_add_time):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Retired date is optional.
        if Keys.GEAR_RETIRE_TIME_KEY in values and len(values[Keys.GEAR_RETIRE_TIME_KEY]) > 0:
            gear_retire_time = values[Keys.GEAR_RETIRE_TIME_KEY]
            if gear_retire_time == 'NaN':
                gear_retire_time = 0
            elif not InputChecker.is_integer(gear_retire_time):
                raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        else:
            gear_retire_time = 0

        result = self.data_mgr.update_gear(self.user_id, gear_id, gear_type, gear_name, gear_description, int(gear_add_time), int(gear_retire_time))
        return result, ""

    def handle_update_gear_defaults(self, values):
        """Called when an API message to update the gear a user wants to associate with an activity type, by default, is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.GEAR_NAME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        activity_type = values[Keys.ACTIVITY_TYPE_KEY]
        if not InputChecker.is_valid_decoded_str(activity_type):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        gear_name = values[Keys.GEAR_NAME_KEY]
        if not InputChecker.is_valid_decoded_str(gear_name):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.update_gear_defaults(self.user_id, activity_type, gear_name)
        return result, ""

    def handle_delete_gear(self, values):
        """Called when an API message to delete gear for a user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.GEAR_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        gear_id = values[Keys.GEAR_ID_KEY]
        if not InputChecker.is_uuid(gear_id):
            raise ApiException.ApiMalformedRequestException("Invalid gear ID.")

        result = self.data_mgr.delete_gear(self.user_id, gear_id)
        return result, ""

    def handle_retire_gear(self, values):
        """Called when an API message to retire gear for a user is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.GEAR_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        gear_id = values[Keys.GEAR_ID_KEY]
        if not InputChecker.is_uuid(gear_id):
            raise ApiException.ApiMalformedRequestException("Invalid gear ID.")

        result = self.data_mgr.update_gear(self.user_id, gear_id, None, None, None, None, time.time())
        return result, ""

    def handle_create_service_record(self, values):
        """Called when an API message to create a service record for an item of gear is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.SERVICE_RECORD_DATE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.SERVICE_RECORD_DESCRIPTION_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        gear_id = values[Keys.GEAR_ID_KEY]
        if not InputChecker.is_uuid(gear_id):
            raise ApiException.ApiMalformedRequestException("Invalid gear ID.")
        service_date = values[Keys.SERVICE_RECORD_DATE_KEY]
        if not InputChecker.is_integer(service_date):
            raise ApiException.ApiMalformedRequestException("Invalid service date.")
        description = values[Keys.SERVICE_RECORD_DESCRIPTION_KEY]
        if not InputChecker.is_valid_decoded_str(description):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.create_service_record(self.user_id, gear_id, service_date, description)
        return result, ""

    def handle_delete_service_record(self, values):
        """Called when an API message to delete a service record for an item of gear is received."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.SERVICE_RECORD_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        gear_id = values[Keys.GEAR_ID_KEY]
        if not InputChecker.is_uuid(gear_id):
            raise ApiException.ApiMalformedRequestException("Invalid gear ID.")
        service_record_id = values[Keys.SERVICE_RECORD_ID_KEY]
        if not InputChecker.is_uuid(service_record_id):
            raise ApiException.ApiMalformedRequestException("Invalid service record ID.")

        result = self.data_mgr.delete_service_record(self.user_id, gear_id, service_record_id)
        return result, ""

    def handle_update_settings(self, values):
        """Called when the user submits a setting change."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        result = True

        # Is there a timestamp associated with this update? If not, use the current time.
        if Keys.TIMESTAMP_KEY in values:
            update_time = datetime.datetime.fromtimestamp(values[Keys.TIMESTAMP_KEY])
        else:
            update_time = datetime.datetime.utcnow()

        # Default privacy/visibility.
        if Keys.DEFAULT_PRIVACY_KEY in values:
            default_privacy = values[Keys.DEFAULT_PRIVACY_KEY].lower()
            if not (default_privacy == Keys.ACTIVITY_VISIBILITY_PUBLIC or default_privacy == Keys.ACTIVITY_VISIBILITY_PRIVATE):
                raise ApiException.ApiMalformedRequestException("Invalid visibility value.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.DEFAULT_PRIVACY_KEY, default_privacy, update_time)
        
        # Metric or imperial?
        if Keys.USER_PREFERRED_UNITS_KEY in values:
            preferred_units = values[Keys.USER_PREFERRED_UNITS_KEY].lower()
            if not (preferred_units == Keys.UNITS_METRIC_KEY or preferred_units == Keys.UNITS_STANDARD_KEY):
                raise ApiException.ApiMalformedRequestException("Invalid units value.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_PREFERRED_UNITS_KEY, preferred_units, update_time)

        # Preferred first day of week.
        if Keys.USER_PREFERRED_FIRST_DAY_OF_WEEK_KEY in values:
            preferred_first_day_of_week = values[Keys.USER_PREFERRED_FIRST_DAY_OF_WEEK_KEY]
            if not preferred_first_day_of_week in Keys.DAYS_OF_WEEK:
                raise ApiException.ApiMalformedRequestException("Invalid day value.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_PREFERRED_FIRST_DAY_OF_WEEK_KEY, preferred_first_day_of_week, update_time)

        # Preferred long run day of the week.
        if Keys.PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY in values:
            preferred_long_run_day = values[Keys.PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY].lower()
            if not InputChecker.is_day_of_week(preferred_long_run_day):
                raise ApiException.ApiMalformedRequestException("Invalid long run day.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY, preferred_long_run_day, update_time)

        # Goal.
        if Keys.GOAL_KEY in values:
            goal = values[Keys.GOAL_KEY]
            if not (goal in Keys.GOALS):
                raise ApiException.ApiMalformedRequestException("Invalid goal.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.GOAL_KEY, goal, update_time)

        # Goal date.
        if Keys.GOAL_DATE_KEY in values:
            if not InputChecker.is_integer(values[Keys.GOAL_DATE_KEY]):
                raise ApiException.ApiMalformedRequestException("Invalid goal date.")
            goal_date = int(values[Keys.GOAL_DATE_KEY])
            result = self.user_mgr.update_user_setting(self.user_id, Keys.GOAL_DATE_KEY, goal_date, update_time)

        # Goal type.
        if Keys.GOAL_TYPE_KEY in values:
            goal_type = values[Keys.GOAL_TYPE_KEY]
            if not (goal_type == Keys.GOAL_TYPE_COMPLETION or goal_type == Keys.GOAL_TYPE_SPEED):
                raise ApiException.ApiMalformedRequestException("Invalid goal type.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.GOAL_TYPE_KEY, goal_type, update_time)

        # Experience level.
        if Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY in values:
            if not InputChecker.is_integer(values[Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY]):
                raise ApiException.ApiMalformedRequestException("Invalid level.")
            level = int(values[Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY])
            if not (level >= 1 and level <= 10):
                raise ApiException.ApiMalformedRequestException("Invalid level.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY, level, update_time)

        # Comfort level with structured training.
        if Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY in values:
            if not InputChecker.is_integer(values[Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY]):
                raise ApiException.ApiMalformedRequestException("Invalid level.")
            level = int(values[Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY])
            if not (level >= 1 and level <= 10):
                raise ApiException.ApiMalformedRequestException("Invalid level.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY, level, update_time)

        return result, ""

    def handle_update_profile(self, values):
        """Called when the user submits a profile change."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        result = True

        # Is there a timestamp associated with this update? If not, use the current time.
        if Keys.TIMESTAMP_KEY in values:
            update_time = datetime.datetime.fromtimestamp(values[Keys.TIMESTAMP_KEY])
        else:
            update_time = datetime.datetime.utcnow()

        # Birthday.
        if Keys.USER_BIRTHDAY_KEY in values:
            birthday = values[Keys.USER_BIRTHDAY_KEY].lower()
            if not InputChecker.is_integer(birthday):
                raise ApiException.ApiMalformedRequestException("Invalid birthday.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_BIRTHDAY_KEY, birthday, update_time)

        # Height.
        if Keys.USER_HEIGHT_KEY in values:
            height = values[Keys.USER_HEIGHT_KEY]
            if not InputChecker.is_float(height):
                raise ApiException.ApiMalformedRequestException("Invalid height.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_HEIGHT_KEY, height, update_time)

        # Weight.
        if Keys.USER_WEIGHT_KEY in values:
            weight = values[Keys.USER_WEIGHT_KEY]
            if not InputChecker.is_float(weight):
                raise ApiException.ApiMalformedRequestException("Invalid weight.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_WEIGHT_KEY, weight, update_time)

        # Gender.
        if Keys.USER_GENDER_KEY in values:
            gender = values[Keys.USER_GENDER_KEY].lower()
            if not (gender == Keys.GENDER_MALE_KEY or gender == Keys.GENDER_FEMALE_KEY):
                raise ApiException.ApiMalformedRequestException("Invalid gender value.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_GENDER_KEY, gender, update_time)

        # Resting Heart Rate.
        if Keys.USER_RESTING_HEART_RATE_KEY in values:
            resting_hr = values[Keys.USER_RESTING_HEART_RATE_KEY].lower()
            if not InputChecker.is_float(resting_hr):
                raise ApiException.ApiMalformedRequestException("Invalid resting heart rate.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_RESTING_HEART_RATE_KEY, float(resting_hr), update_time)

        # Max Heart Rate.
        if Keys.USER_MAXIMUM_HEART_RATE_KEY in values:
            max_hr = values[Keys.USER_MAXIMUM_HEART_RATE_KEY].lower()
            if not InputChecker.is_float(max_hr):
                raise ApiException.ApiMalformedRequestException("Invalid max heart rate.")
            result = self.user_mgr.update_user_setting(self.user_id, Keys.USER_MAXIMUM_HEART_RATE_KEY, float(max_hr), update_time)

        return result, ""

    def handle_update_visibility(self, values):
        """Called when the user updates the visibility of an activity."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")
        if Keys.ACTIVITY_VISIBILITY_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Visibility not specified.")

        visibility = values[Keys.ACTIVITY_VISIBILITY_KEY].lower()
        if not (visibility == Keys.ACTIVITY_VISIBILITY_PUBLIC or visibility == Keys.ACTIVITY_VISIBILITY_PRIVATE):
            raise ApiException.ApiMalformedRequestException("Invalid visibility value.")

        result = self.data_mgr.update_activity_visibility(values[Keys.ACTIVITY_ID_KEY], visibility)
        return result, ""

    def handle_refresh_analysis(self, values):
        """Called when the user wants to recalculate the summary data."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        activity = self.data_mgr.retrieve_activity(activity_id)
        if not activity:
            raise ApiException.ApiMalformedRequestException("Invalid activity.")

        activity_user_id, _, _ = self.user_mgr.get_activity_user(activity)
        self.data_mgr.analyze_activity(activity, activity_user_id)
        return True, ""

    def handle_generate_workout_plan_for_user(self):
        """Called when the user wants to generate a workout plan."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        self.data_mgr.generate_workout_plan_for_user(self.user_id)
        return True, ""

    def handle_generate_workout_plan_from_inputs(self, values):
        """Called when the user wants to generate a workout plan."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        self.data_mgr.generate_workout_plan_from_inputs(self.user_id)
        return True, ""

    def handle_generate_api_key(self, values):
        """Generates a new API key for the specified user."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        result, api_key = self.data_mgr.generate_api_key_for_user(self.user_id)
        return result, api_key

    def handle_delete_api_key(self, values):
        """Deletes the specified API key."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.API_KEY not in values:
            raise ApiException.ApiMalformedRequestException("A key was not specified.")

        api_key = values[Keys.API_KEY]
        result = self.data_mgr.delete_api_key(self.user_id, api_key)
        return result, api_key

    def handle_merge_activities(self, values):
        """Takes two files and attempts to merge them."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.UPLOADED_FILE1_DATA_KEY not in values:
            raise ApiException.ApiMalformedRequestException("File data not specified.")
        if Keys.UPLOADED_FILE2_DATA_KEY not in values:
            raise ApiException.ApiMalformedRequestException("File data not specified.")

        # Decode the parameters.
        uploaded_file1_data = unquote_plus(values[Keys.UPLOADED_FILE1_DATA_KEY])
        uploaded_file2_data = unquote_plus(values[Keys.UPLOADED_FILE2_DATA_KEY])

        # Check for empty.
        if len(uploaded_file1_data) == 0:
            raise ApiException.ApiMalformedRequestException('Empty file data.')
        if len(uploaded_file2_data) == 0:
            raise ApiException.ApiMalformedRequestException('Empty file data.')

        # Parse the file and store it's contents in the database.
        merged_data = self.data_mgr.merge_activities(self.user_id, uploaded_file1_data, uploaded_file2_data)
        return True, merged_data

    def handle_list_planned_workouts(self, values):
        """Called when the user wants wants a list of their planned workouts. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        # Fetch and validate the activity start and end times (optional).
        start_time = None
        end_time = None
        if Keys.START_DATE_KEY in values:
            start_time = int(datetime.datetime.strptime(values[Keys.START_DATE_KEY], '%Y-%m-%d').strftime("%s"))
        if Keys.END_DATE_KEY in values:
            end_time = int(datetime.datetime.strptime(values[Keys.END_DATE_KEY], '%Y-%m-%d').strftime("%s"))
        if Keys.START_TIME_KEY in values:
            start_time = values[Keys.START_TIME_KEY]
            if InputChecker.is_integer(start_time):
                start_time = int(start_time)
            else:
                raise ApiException.ApiMalformedRequestException("Invalid start time.")
        if Keys.END_TIME_KEY in values:
            end_time = values[Keys.END_TIME_KEY]
            if InputChecker.is_integer(end_time):
                end_time = int(end_time)
            else:
                raise ApiException.ApiMalformedRequestException("Invalid end time.")

        # Get the workouts that belong to the logged in user.
        workouts = self.data_mgr.retrieve_planned_workouts_for_user(self.user_id, start_time, end_time)

        # Convert the activities list to an array of JSON objects for return to the client.
        matched_workouts = []
        if workouts is not None and isinstance(workouts, list):
            for workout in workouts:
                workout_dict = workout.to_dict()
                workout_dict['url'] = self.root_url + "/workout/" + str(workout.workout_id)
                matched_workouts.append(workout_dict)
        json_result = json.dumps(matched_workouts, ensure_ascii=False)
        return True, json_result

    def handle_list_interval_workouts(self, values):
        """Called when the user wants wants a list of their interval workouts. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        workouts = self.data_mgr.retrieve_interval_workouts_for_user(self.user_id)
        json_result = json.dumps(workouts)
        return True, json_result

    def handle_create_pace_plan(self, values):
        """Called when the user is uploading a pace plan, typically from the mobile app."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.PACE_PLAN_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_NAME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_TARGET_PACE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_TARGET_DISTANCE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_DISPLAY_UNITS_PACE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_DISPLAY_UNITS_DISTANCE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_SPLITS_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        if Keys.PACE_PLAN_LAST_UPDATED_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        plan_id = unquote_plus(values[Keys.PACE_PLAN_ID_KEY])
        if not InputChecker.is_uuid(plan_id):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        plan_name = unquote_plus(values[Keys.PACE_PLAN_NAME_KEY])
        if not InputChecker.is_valid_decoded_str(plan_name):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        target_pace = unquote_plus(values[Keys.PACE_PLAN_TARGET_PACE_KEY])
        if not InputChecker.is_float(target_pace):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        target_distance = unquote_plus(values[Keys.PACE_PLAN_TARGET_DISTANCE_KEY])
        if not InputChecker.is_float(target_distance):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        target_pace_units = unquote_plus(values[Keys.PACE_PLAN_DISPLAY_UNITS_PACE_KEY])
        if not InputChecker.is_float(target_pace_units):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        target_distance_units = unquote_plus(values[Keys.PACE_PLAN_DISPLAY_UNITS_DISTANCE_KEY])
        if not InputChecker.is_float(target_distance_units):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        splits = unquote_plus(values[Keys.PACE_PLAN_SPLITS_KEY])
        if not InputChecker.is_float(splits):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        last_updated_time = unquote_plus(values[Keys.PACE_PLAN_LAST_UPDATED_KEY])
        if not InputChecker.is_integer(last_updated_time):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.create_pace_plan(self.user_id, plan_id, plan_name, target_pace, target_distance, target_pace_units, target_distance_units, splits, last_updated_time)
        return result, ""

    def handle_delete_pace_plan(self, values):
        """Called when the user wants to delete a pace plan."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.PACE_PLAN_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        plan_id = values[Keys.PACE_PLAN_ID_KEY]
        if not InputChecker.is_uuid(plan_id):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        result = self.data_mgr.delete_pace_plan(self.user_id, plan_id)
        return result, ""

    def handle_list_pace_plans(self, values):
        """Called when the user wants wants a list of their pace plans. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        pace_plans = self.data_mgr.retrieve_pace_plans_for_user(self.user_id)
        json_result = json.dumps(pace_plans)
        return True, json_result

    def handle_get_workout_ical_url(self, values):
        """Called when the user wants a link to the ical url for their planned workouts."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        calendar_id = self.data_mgr.retrieve_workouts_calendar_id_for_user(self.user_id)
        url = self.root_url + "/ical/" + str(calendar_id)
        return True, url

    def handle_get_location_description(self, values):
        """Called when the user wants get the political location that corresponds to an activity."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")

        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        location_description = self.data_mgr.get_location_description(activity_id)
        return True, str(location_description)

    def handle_get_location_summary(self, values):
        """Called when the user wants get the summary of all political locations in which activities have occurred. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        username = self.user_mgr.get_logged_in_user()
        _, _, user_realname = self.user_mgr.retrieve_user(username)

        user_activities = self.data_mgr.retrieve_user_activity_list(self.user_id, user_realname, None, None, None)
        heat_map = self.data_mgr.compute_location_heat_map(user_activities)
        return True, json.dumps(heat_map)

    def handle_get_activity_hash_from_id(self, values):
        """Given the activity hash, return sthe activity ID, or an error if not found. Only looks at the logged in user's activities."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")

        # Activity ID from user.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Hash from database.
        summary_data = self.data_mgr.retrieve_activity_summary(activity_id)
        if Keys.ACTIVITY_HASH_KEY not in summary_data:
            raise ApiException.ApiMalformedRequestException("Hash not found.")

        return True, str(summary_data[Keys.ACTIVITY_HASH_KEY])

    def handle_has_activity(self, values):
        """Given the activity hash, return sthe activity ID, or an error if not found. Only looks at the logged in user's activities."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_ID_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity ID not specified.")
        if Keys.ACTIVITY_HASH_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity hash not specified.")

        # Activity ID from user.
        activity_id = values[Keys.ACTIVITY_ID_KEY]
        if not InputChecker.is_uuid(activity_id):
            raise ApiException.ApiMalformedRequestException("Invalid activity ID.")

        # Activity hash from user.
        activity_hash = values[Keys.ACTIVITY_HASH_KEY]
        if not InputChecker.is_hex_str(activity_hash):
            raise ApiException.ApiMalformedRequestException("Invalid activity hash.")

        # Anything in the database?
        exists = self.data_mgr.activity_exists(activity_id)
        if not exists:
            return True, json.dumps( { Keys.CODE_KEY: 0, Keys.ACTIVITY_ID_KEY: activity_id } ) # Activity does not exist
        summary_data = self.data_mgr.retrieve_activity_summary(activity_id)
        if summary_data is None:
            return True, json.dumps( { Keys.CODE_KEY: 1, Keys.ACTIVITY_ID_KEY: activity_id } ) # Activity exists, hash not computed

        # Hash from database.
        if Keys.ACTIVITY_HASH_KEY not in summary_data:
            return True, json.dumps( { Keys.CODE_KEY: 1, Keys.ACTIVITY_ID_KEY: activity_id } ) # Activity exists, hash not computed
        hash_from_db = summary_data[Keys.ACTIVITY_HASH_KEY]
        if hash_from_db != activity_hash:
            return True, json.dumps( { Keys.CODE_KEY: 2, Keys.ACTIVITY_ID_KEY: activity_id } ) # Activity exists, has does not match

        return True, json.dumps( { Keys.CODE_KEY: 3, Keys.ACTIVITY_ID_KEY: activity_id } ) # Activity exists, has matches

    def handle_list_personal_records(self, values):
        """Returns the user's personal records. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        if Keys.SECONDS in values:
            num_seconds = int(values[Keys.SECONDS])
        else:
            num_seconds = None

        unit_system = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_PREFERRED_UNITS_KEY)
        cycling_bests, running_bests, _, _ = self.data_mgr.retrieve_recent_bests(self.user_id, num_seconds)

        for item in cycling_bests:
            seconds = cycling_bests[item][0]
            activity_id = cycling_bests[item][1]
            formatted_time = Units.convert_to_string_in_specified_unit_system(unit_system, seconds, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, item)
            cycling_bests[item] = formatted_time, activity_id, seconds
        for item in running_bests:
            seconds = running_bests[item][0]
            activity_id = running_bests[item][1]
            formatted_time = Units.convert_to_string_in_specified_unit_system(unit_system, seconds, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, item)
            running_bests[item] = formatted_time, activity_id, seconds

        bests = {}
        bests[Keys.TYPE_CYCLING_KEY] = cycling_bests
        bests[Keys.TYPE_RUNNING_KEY] = running_bests
        return True, json.dumps(bests)

    def handle_get_running_paces(self, values):
        """Returns the user's estimated running paces. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.BEST_5K not in values:
            raise ApiException.ApiMalformedRequestException("Best 5K not specified.")

        calc = TrainingPaceCalculator.TrainingPaceCalculator()
        unit_system = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_PREFERRED_UNITS_KEY)
        run_paces = calc.calc_from_race_distance_in_meters(5000, float(values[Keys.BEST_5K]) / 60)
        converted_paces = {}
        for run_pace in run_paces:
            converted_paces[run_pace] = Units.convert_to_string_in_specified_unit_system(unit_system, run_paces[run_pace], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, run_pace)
        return True, json.dumps(converted_paces)

    def handle_get_run_race_predictions(self, values):
        pass

    def handle_get_distance_for_tag(self, values):
        """Returns the amount of distance logged to activities with the given tag. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_TAG_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Tag not specified.")

        tag = values[Keys.ACTIVITY_TAG_KEY]
        if not InputChecker.is_valid_decoded_str(tag):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        tags = []
        tags.append(tag)

        converted_distances = []
        unit_system = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_PREFERRED_UNITS_KEY)
        gear_distances = self.data_mgr.distance_for_tags(self.user_id, tags)
        for gear_name in gear_distances:
            converted_distance = Units.convert_to_string_in_specified_unit_system(unit_system, gear_distances[gear_name], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, Keys.TOTAL_DISTANCE)
            converted_distances.append({gear_name: converted_distance})
        return True, json.dumps(converted_distances)

    def handle_get_task_statuses(self, values):
        """Returns a description of all deferred tasks for the logged in user. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        tasks = self.data_mgr.retrieve_deferred_tasks(self.user_id)
        return True, json.dumps(tasks)

    def handle_get_record_progression(self, values):
        """Returns an ordered list containing the time and activity ID of the user's record progression for the specified record and activity type, i.e. best running 5K. Result is a JSON string."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.ACTIVITY_TYPE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Activity type specified.")
        if Keys.RECORD_NAME_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Record name not specified.")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise ApiException.ApiMalformedRequestException("Empty username.")

        # Get the user details.
        _, _, user_realname = self.user_mgr.retrieve_user(username)

        # Get the user activity list, sorted by timestamp.
        user_activities = self.data_mgr.retrieve_user_activity_list(self.user_id, user_realname, None, None, None)

        activity_type = values[Keys.ACTIVITY_TYPE_KEY]
        if not InputChecker.is_valid_decoded_str(activity_type):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")
        record_name = values[Keys.RECORD_NAME_KEY]
        if not InputChecker.is_valid_decoded_str(record_name):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        records = self.data_mgr.compute_progression(self.user_id, user_activities, activity_type, record_name)
        unit_system = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_PREFERRED_UNITS_KEY)
        for record in records:
            record[0] = Units.convert_to_string_in_specified_unit_system(unit_system, record[0], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, record_name)
        return True, json.dumps(records)

    def handle_get_user_setting(self, values):
        """Returns the value associated with the specified user setting."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.REQUESTED_SETTING_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Setting not specified.")

        setting = values[Keys.REQUESTED_SETTING_KEY]
        setting_value = self.user_mgr.retrieve_user_setting(self.user_id, setting)
        return True, str(setting_value)

    def handle_get_user_settings(self, values):
        """Returns the value associated with the specified user settings. Settings are a list of strings."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()
        if Keys.REQUESTED_SETTINGS_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Settings not specified.")

        settings = values[Keys.REQUESTED_SETTINGS_KEY].split(',')
        setting_values = self.user_mgr.retrieve_user_settings(self.user_id, settings)
        return True, json.dumps(setting_values)

    def handle_estimate_vo2_max(self):
        """Returns the user's estimated VO2 Max, based on their resting and max heart rates."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        resting_hr = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_RESTING_HEART_RATE_KEY)
        estimated_max_hr = self.user_mgr.retrieve_user_setting(self.user_id, Keys.ESTIMATED_MAX_HEART_RATE_KEY)
        estimated_vo2_max = self.data_mgr.estimate_vo2_max(resting_hr, estimated_max_hr)
        return True, json.dumps(estimated_vo2_max)

    def handle_estimate_ftp(self):
        """Returns the user's estimated FTP."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        ftp = self.user_mgr.estimate_ftp(self.user_id)
        return True, json.dumps(ftp)

    def handle_estimate_bmi(self):
        """Returns the user's estimated BMI."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        weight_metric = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_WEIGHT_KEY)
        height_metric = self.user_mgr.retrieve_user_setting(self.user_id, Keys.USER_HEIGHT_KEY)
        bmi = self.data_mgr.estimate_bmi(weight_metric, height_metric)
        return True, json.dumps(bmi)

    def handle_list_power_zones(self, values):
        """Returns power zones corresponding to the specified FTP value."""
        if Keys.ESTIMATED_CYCLING_FTP_KEY not in values:
            raise ApiException.ApiMalformedRequestException("FTP not specified.")

        ftp = values[Keys.ESTIMATED_CYCLING_FTP_KEY]
        if not InputChecker.is_float(ftp):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        zones = self.data_mgr.retrieve_power_training_zones(float(ftp))
        return True, json.dumps(zones)

    def handle_list_hr_zones(self, values):
        """Returns heart rate zones corresponding to the specified resting heart rate value."""
        if Keys.ESTIMATED_MAX_HEART_RATE_KEY not in values:
            raise ApiException.ApiMalformedRequestException("Maximum heart rate not specified.")

        max_hr = values[Keys.ESTIMATED_MAX_HEART_RATE_KEY]
        if not InputChecker.is_float(max_hr):
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        # Convert to float and sanity check.
        max_hr = float(max_hr)
        if max_hr < 1.0:
            raise ApiException.ApiMalformedRequestException("Invalid parameter.")

        zones = self.data_mgr.retrieve_heart_rate_zones(max_hr)
        return True, json.dumps(zones)

    def handle_list_api_keys(self):
        """Returns a list of API keys assigned to the current user."""
        if self.user_id is None:
            raise ApiException.ApiNotLoggedInException()

        keys = self.user_mgr.retrieve_api_keys(self.user_id)
        return True, json.dumps(keys)

    def handle_list_activity_types(self):
        """Returns the list of all activity types the software understands."""
        return True, json.dumps(self.data_mgr.retrieve_activity_types())

    def handle_api_1_0_get_request(self, request, values):
        """Called to parse a version 1.0 API GET request."""
        if request == 'activity_track':
            return self.handle_retrieve_activity_track(values)
        elif request == 'activity_metadata':
            return self.handle_retrieve_activity_metadata(values)
        elif request == 'activity_sensordata':
            return self.handle_retrieve_activity_sensordata(values)
        elif request == 'activity_summarydata':
            return self.handle_retrieve_activity_summarydata(values)
        elif request == 'login_status':
            return self.handle_login_status(values)
        elif request == 'list_devices':
            return self.handle_list_devices(values)
        elif request == 'list_all_activities':
            return self.handle_list_activities(values, True)
        elif request == 'list_my_activities':
            return self.handle_list_activities(values, False)
        elif request == 'list_activity_photos':
            return self.handle_list_activity_photos(values)
        elif request == 'list_pending_friends':
            return self.list_pending_friends(values)
        elif request == 'list_friends':
            return self.list_friends(values)
        elif request == 'list_tags':
            return self.handle_list_tags(values)
        elif request == 'list_comments':
            return self.handle_list_comments(values)
        elif request == 'list_gear':
            return self.handle_list_gear(values)
        elif request == 'list_gear_defaults':
            return self.handle_list_gear_defaults(values)
        elif request == 'list_planned_workouts':
            return self.handle_list_planned_workouts(values)
        elif request == 'list_interval_workouts':
            return self.handle_list_interval_workouts(values)
        elif request == 'list_pace_plans':
            return self.handle_list_pace_plans(values)
        elif request == 'export_activity':
            return self.handle_export_activity(values)
        elif request == 'export_workout':
            return self.handle_export_workout(values)
        elif request == 'get_workout_ical_url':
            return self.handle_get_workout_ical_url(values)
        elif request == 'get_location_description':
            return self.handle_get_location_description(values)
        elif request == 'get_location_summary':
            return self.handle_get_location_summary(values)
        elif request == 'activity_hash_from_id':
            return self.handle_get_activity_hash_from_id(values)
        elif request == 'has_activity':
            return self.handle_has_activity(values)
        elif request == 'list_personal_records':
            return self.handle_list_personal_records(values)
        elif request == 'get_running_paces':
            return self.handle_get_running_paces(values)
        elif request == 'get_distance_for_tag':
            return self.handle_get_distance_for_tag(values)
        elif request == 'get_task_statuses':
            return self.handle_get_task_statuses(values)
        elif request == 'get_record_progression':
            return self.handle_get_record_progression(values)
        elif request == 'get_user_setting':
            return self.handle_get_user_setting(values)
        elif request == 'get_user_settings':
            return self.handle_get_user_settings(values)
        elif request == 'estimate_vo2_max':
            return self.handle_estimate_vo2_max()
        elif request == 'estimate_ftp':
            return self.handle_estimate_ftp()
        elif request == 'estimate_bmi':
            return self.handle_estimate_bmi()
        elif request == 'list_power_zones':
            return self.handle_list_power_zones(values)
        elif request == 'list_hr_zones':
            return self.handle_list_hr_zones(values)
        elif request == 'list_api_keys':
            return self.handle_list_api_keys()
        elif request == 'list_activity_types':
            return self.handle_list_activity_types()
        return False, ""

    def handle_api_1_0_post_request(self, request, values):
        """Called to parse a version 1.0 API POST request."""
        if request == 'update_status':
            return self.handle_update_status(values)
        elif request == 'update_activity_metadata':
            return self.handle_update_activity_metadata(values)
        elif request == 'login':
            return self.handle_login(values)
        elif request == 'create_login':
            return self.handle_create_login(values)
        elif request == 'logout':
            return self.handle_logout(values)
        elif request == 'update_email':
            return self.handle_update_email(values)
        elif request == 'update_password':
            return self.handle_update_password(values)
        elif request == 'delete_users_gear':
            return self.handle_delete_users_gear(values)
        elif request == 'delete_users_activities':
            return self.handle_delete_users_activities(values)
        elif request == 'delete_user':
            return self.handle_delete_user(values)
        elif request == 'delete_activity':
            return self.handle_delete_activity(values)
        elif request == 'add_activity':
            return self.handle_add_activity(values)
        elif request == 'upload_activity_file':
            return self.handle_upload_activity_file(values)
        elif request == 'upload_activity_photo':
            return self.handle_upload_activity_photo(values)
        elif request == 'delete_activity_photo':
            return self.handle_delete_activity_photo(values)
        elif request == 'create_tags_on_activity':
            return self.handle_create_tags_on_activity(values)
        elif request == 'delete_tag_from_activity':
            return self.handle_delete_tag_from_activity(values)
        elif request == 'list_matched_users':
            return self.handle_list_matched_users(values)
        elif request == 'request_to_be_friends':
            return self.handle_friend_request(values)
        elif request == 'confirm_request_to_be_friends':
            return self.handle_confirm_friend_request(values)
        elif request == 'unfriend':
            return self.handle_unfriend_request(values)
        elif request == 'export_activity':
            return self.handle_export_activity(values)
        elif request == 'claim_device':
            return self.handle_claim_device(values)
        elif request == 'create_tag':
            return self.handle_create_tag(values)
        elif request == 'delete_tag':
            return self.handle_delete_tag(values)
        elif request == 'create_comment':
            return self.handle_create_comment(values)
        elif request == 'create_gear':
            return self.handle_create_gear(values)
        elif request == 'update_gear':
            return self.handle_update_gear(values)
        elif request == 'update_gear_defaults':
            return self.handle_update_gear_defaults(values)
        elif request == 'delete_gear':
            return self.handle_delete_gear(values)
        elif request == 'retire_gear':
            return self.handle_retire_gear(values)
        elif request == 'create_service_record':
            return self.handle_create_service_record(values)
        elif request == 'delete_service_record':
            return self.handle_delete_service_record(values)
        elif request == 'create_pace_plan':
            return self.handle_create_pace_plan(values)        
        elif request == 'delete_pace_plan':
            return self.handle_delete_pace_plan(values)        
        elif request == 'update_settings':
            return self.handle_update_settings(values)
        elif request == 'update_profile':
            return self.handle_update_profile(values)
        elif request == 'update_visibility':
            return self.handle_update_visibility(values)
        elif request == 'refresh_analysis':
            return self.handle_refresh_analysis(values)
        elif request == 'generate_workout_plan':
            return self.handle_generate_workout_plan_for_user()
        elif request == 'generate_workout_plan_from_inputs':
            return self.handle_generate_workout_plan_from_inputs(values)
        elif request == 'generate_api_key':
            return self.handle_generate_api_key(values)
        elif request == 'delete_api_key':
            return self.handle_delete_api_key(values)
        elif request == 'merge_activities':
            return self.handle_merge_activities(values)
        return False, ""

    def handle_api_1_0_request(self, verb, request, values):
        """Called to parse a version 1.0 API message."""
        if self.user_id is None:
            if Keys.SESSION_KEY in values:
                username = self.user_mgr.get_logged_in_user_from_cookie(values[Keys.SESSION_KEY])
                if username is not None:
                    self.user_id, _, _ = self.user_mgr.retrieve_user(username)

        if verb == 'GET':
            return self.handle_api_1_0_get_request(request, values)
        elif verb == 'POST':
            # Flatten the array of dictionaries into a single dictionary.
            if isinstance(values, list):
                values = {k: v for d in values for k, v in d.items()}
            return self.handle_api_1_0_post_request(request, values)
        return False, ""
