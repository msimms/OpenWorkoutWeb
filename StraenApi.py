# Copyright 2017 Michael J Simms
"""API request handlers"""

import cherrypy
import cgi
import json
import logging
import time
import StraenDb
import StraenKeys

g_not_meta_data = ["DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy"]

class StraenApi(object):
    """Class for managing API messages."""

    def __init__(self, root_dir):
        super(StraenApi, self).__init__()
        self.database = StraenDb.MongoDatabase(root_dir)

    def parse_json_loc_obj(self, json_obj):
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
                self.database.create_location(device_str, activity_id, date_time, lat, lon, alt)
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
                        self.database.create_sensordata(device_str, activity_id, date_time, key, value)
                    elif key in [StraenKeys.CURRENT_SPEED_KEY, StraenKeys.CURRENT_PACE_KEY]:
                        self.database.create_metadata(device_str, activity_id, date_time, key, value)

            # Update the user device association.
            if len(username) > 0:
                user_id, _, _ = self.database.retrieve_user(username)
                user_devices = self.database.retrieve_user_devices(user_id)
                if user_devices is not None and device_str not in user_devicees:
                    self.database.create_user_device(user_id, device_str)
        except ValueError, e:
            cherrypy.log.error("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj), 'EXEC', logging.WARNING)
        except KeyError, e:
            cherrypy.log.error("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj), 'EXEC', logging.WARNING)
        except:
            cherrypy.log.error("Error parsing JSON location data. JSON object = " + str(json_obj), 'EXEC', logging.WARNING)

    def handle_update_location(self, locations):
        """Called when the a new GPS point is received from the app."""
        for location_obj in locations:
            self.parse_json_loc_obj(location_obj)

    def handle_upload_activity_file(self, args):
        pass

    def handle_add_tag_to_activity(self, args):
        pass

    def handle_delete_tag_from_activity(self, args):
        pass

    def handle_api_1_0_request(self, args, values):
        """Called to parse a version 1.0 API message."""
        if len(args) > 0:
            request = args[0]
            if request == 'update_location':
                if "locatons" in values:
                    self.handle_update_location(values["locations"])
            if request == 'upload_activity_file':
                self.handle_upload_activity_file(args)
            elif request == 'add_tag_to_activity':
                self.handle_add_tag_to_activity(args)
            elif request == 'delete_tag_from_activity':
                self.handle_delete_tag_from_activity(args)
                