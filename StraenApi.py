# Copyright 2017 Michael J Simms
"""API request handlers"""

import json
import logging
import time
import uuid
import cherrypy
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

    def parse_json_loc_obj(self, json_obj):
        """Helper function that parses the JSON object, which contains location data, and updates the database."""
        try:
            # Parse required identifiers.
            device_str = json_obj["DeviceId"]
            activity_id = json_obj["ActivityId"]

            # Parse optional identifiers.
            username = ""
            try:
                username = json_obj["User Name"]
            except:
                pass

            # Parse the metadata looking for the timestamp.
            date_time = time.time()
            try:
                time_str = json_obj["Time"]
                date_time = int(time_str)
            except:
                pass

            # Parse the location data.
            try:
                lat = json_obj["Latitude"]
                lon = json_obj["Longitude"]
                alt = json_obj["Altitude"]
                self.data_mgr.create_location(device_str, activity_id, date_time, lat, lon, alt)
            except ValueError, e:
                cherrypy.log.error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj), 'EXEC', logging.WARNING)
            except KeyError, e:
                cherrypy.log.error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj), 'EXEC', logging.WARNING)
            except:
                cherrypy.log.error("Error parsing JSON location data. JSON object = " + str(json_obj), 'EXEC', logging.WARNING)

            # Parse the rest of the data, which will be a combination of metadata and sensor data.
            for item in json_obj.iteritems():
                key = item[0]
                value = item[1]
                if not key in g_not_meta_data:
                    if key in [StraenKeys.CADENCE_KEY, StraenKeys.HEART_RATE_KEY, StraenKeys.POWER_KEY]:
                        self.data_mgr.create_sensordata(device_str, activity_id, date_time, key, value)
                    elif key in [StraenKeys.CURRENT_SPEED_KEY, StraenKeys.CURRENT_PACE_KEY]:
                        self.data_mgr.create_metadata(device_str, activity_id, date_time, key, value)

            # Update the user device association.
            if len(username) > 0:
                user_id, _, _ = self.user_mgr.retrieve_user(username)
                user_devices = self.user_mgr.retrieve_user_devices(user_id)
                if user_devices is not None and device_str not in user_devices:
                    self.user_mgr.create_user_device(user_id, device_str)
        except ValueError, e:
            cherrypy.log.error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj), 'EXEC', logging.WARNING)
        except KeyError, e:
            cherrypy.log.error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj), 'EXEC', logging.WARNING)
        except:
            cherrypy.log.error("Error parsing JSON location data. JSON object = " + str(json_obj), 'EXEC', logging.WARNING)

    def handle_update_location(self, values):
        """Called when an API message to update the location of a device is received."""
        locations_str = values.keys()[0]
        if "locations" in locations_str:
            json_obj = json.loads(locations_str)
            locations = json_obj["locations"]
            for location_obj in locations:
                self.parse_json_loc_obj(location_obj)
            return True, ""
        return False, ""

    def handle_add_time_and_distance_activity(self, values):
        """Called when an API message to add a new activity based on time and distance is received."""
        if StraenKeys.TIME_KEY not in values:
            return False, "Time not specified."
        if StraenKeys.DISTANCE_KEY not in values:
            return False, "Distance not specified."

        activity_id = str(uuid.uuid4())
        return True, ""

    def handle_add_sets_and_reps_activity(self, values):
        """Called when an API message to add a new activity based on sets and reps is received."""
        if StraenKeys.SETS_KEY not in values:
            return False, "Sets not specified."

        activity_id = str(uuid.uuid4())
        sets = values[StraenKeys.SETS_KEY]
        print sets
        return True, ""

    def handle_add_activity(self, values):
        """Called when an API message to add a new activity is received."""
        if self.user_id is None:
            return False, "Not logged in."
        if StraenKeys.ACTIVITY_TYPE_KEY not in values:
            return False, "Activity type not specified."

        switcher = {
            StraenKeys.TYPE_RUNNING_KEY : self.handle_add_time_and_distance_activity,
            StraenKeys.TYPE_CYCLING_KEY : self.handle_add_time_and_distance_activity,
            StraenKeys.TYPE_SWIMMING_KEY : self.handle_add_time_and_distance_activity,
            StraenKeys.TYPE_PULL_UPS_KEY : self.handle_add_sets_and_reps_activity
        }

        func = switcher.get(values[StraenKeys.ACTIVITY_TYPE_KEY], lambda: "Invalid activity type")
        return func(values)

    def handle_upload_activity_file(self, values):
        """Called when an API message to upload a file is received."""
        if self.user_id is None:
            return False, "Not logged in."
        return True, ""

    def handle_add_tag_to_activity(self, values):
        """Called when an API message to add a tag to an activity is received."""
        if self.user_id is None:
            return False, "Not logged in."
        return True, ""

    def handle_delete_tag_from_activity(self, values):
        """Called when an API message to delete a tag from an activity is received."""
        if self.user_id is None:
            return False, "Not logged in."
        return True, ""

    def handle_list_matched_users(self, values):
        """Called when an API message to list users is received."""
        if self.user_id is None:
            return False, "Not logged in."
        if 'searchname' not in values:
            return False, "Invalid parameter."

        search_name = values['searchname']
        search_name_len = len(search_name)
        if search_name_len < 3:
            return False, "Search name is too short."
        if search_name_len > 100:
            return False, "Search name is too long."
        matched_users = self.user_mgr.retrieve_matched_users(search_name)[:100] # Limit the number of results
        json_result = json.dumps(matched_users, ensure_ascii=False)
        return True, json_result

    def handle_request_to_follow(self, values):
        """Called when an API message request to follow another user is received."""
        if self.user_id is None:
            return False, "Not logged in."
        if 'target_email' not in values:
            return False, "Invalid parameter."

        target_email = values['target_email']
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            return False, "Target user does not exist."
        if self.user_mgr.request_to_follow(self.user_id, target_email):
            return True, ""
        return False, ""

    def handle_unfollow(self, values):
        """Called when an API message request to follow another user is received."""
        if self.user_id is None:
            return False, "Not logged in."
        if 'target_email' not in values:
            return False, "Invalid parameter."

        target_email = values['target_email']
        target_id, _, _ = self.user_mgr.retrieve_user(target_email)
        if target_id is None:
            return False, "Target user does not exist."
        return False, ""

    def handle_export_activity(self, values):
        """Called when an API message request to follow another user is received."""
        if self.user_id is None:
            return False, "Not logged in."
        if 'activity_id' not in values:
            return False, "Invalid parameter."

        exporter = Exporter.Exporter()
        result = exporter.export(self.data_mgr, values['activity_id'])
        return True, result

    def handle_claim_device(self, values):
        """Called when an API message request to follow another user is received."""
        if self.user_id is None:
            return False, "Not logged in."
        if 'device_id' not in values:
            return False, "Invalid parameter."

        self.data_mgr.create_user_device(self.user_id, values['device_id'])
        return True, ""

    def handle_api_1_0_request(self, args, values):
        """Called to parse a version 1.0 API message."""
        if len(args) <= 0:
            return False, ""

        request = args[0]
        if request == 'update_location':
            return self.handle_update_location(values)
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
        elif request == 'request_to_follow':
            return self.handle_request_to_follow(values)
        elif request == 'unfollow':
            return self.handle_unfollow(values)
        elif request == 'export_activity':
            return self.handle_export_activity(values)
        elif request == 'claim_device':
            return self.handle_claim_device(values)
        return False, ""
