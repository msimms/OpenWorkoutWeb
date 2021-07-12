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
"""Parses GPX and TCX files, passing the contents to a ActivityWriter object."""

import calendar
import csv
import datetime
import fitparse
import gpxpy
import logging
import os
import traceback
import sys
from lxml import objectify

import Keys

class ActivityWriter(object):
    """Base class for any class that handles data read from the Importer."""

    def is_duplicate_activity(self, user_id, start_time, optional_activity_id):
        """Inherited from ActivityWriter. Returns TRUE if the activity appears to be a duplicate of another activity. Returns FALSE otherwise."""
        return False

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time, desired_activity_id):
        """Pure virtual method for starting a location stream - creates the activity ID for the specified user."""
        pass

    def create_activity_track(self, device_str, activity_id, track_name, track_description):
        """Pure virtual method for starting a location track - creates the activity ID for the specified user."""
        pass

    def create_activity_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Pure virtual method for processing a location read by the importer."""
        pass

    def create_activity_locations(self, device_str, activity_id, locations):
        """Pure virtual method for processing multiple location reads. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        pass

    def create_activity_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Pure virtual method for processing a sensor reading from the importer."""
        pass

    def create_activity_sensor_readings(self, activity_id, sensor_type, values):
        """Pure virtual method for processing multiple sensor readings. 'values' is an array of arrays in the form [time, value]."""
        pass

    def create_activity_event(self, activity_id, event):
        """Pure virtual method for processing an event reading. 'event' is a dictionary describing an event."""
        pass

    def create_activity_events(self, activity_id, events):
        """Pure virtual method for processing multiple event readings. 'events' is an array of dictionaries in which each dictionary describes an event."""
        pass

    def finish_activity(self, activity_id, end_time):
        """Pure virtual method for any post-processing."""
        pass

class Importer(object):
    """Importer for GPX and TCX location files."""

    def __init__(self, activity_writer):
        super(Importer, self).__init__()
        self.activity_writer = activity_writer

    @staticmethod
    def normalize_activity_type(activity_type, sub_activity_type, file_name):
        """Takes the various activity names that appear in GPX and TCX files and normalizes to the ones used in this app."""
        if activity_type is None:
            return Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY

        lower_activity_type = activity_type.lower()
        lower_sub_activity_type = sub_activity_type.lower()
        file_name_parts = file_name.lower().split(' ')

        if lower_activity_type == Keys.TYPE_RUNNING_KEY.lower():
            # Look for words that indicate that the activity may be from a virtual running service, such as Zwift.
            if 'zwift' in file_name_parts:
                return Keys.TYPE_VIRTUAL_RUNNING_KEY
            return Keys.TYPE_RUNNING_KEY
        elif lower_activity_type == Keys.TYPE_HIKING_KEY.lower():
            return Keys.TYPE_HIKING_KEY
        elif lower_activity_type == Keys.TYPE_WALKING_KEY.lower():
            return Keys.TYPE_WALKING_KEY
        elif lower_activity_type == Keys.TYPE_CYCLING_KEY.lower() or lower_activity_type == 'biking':
            # Look for words that indicate that the activity may be from a virtual cycling service, such as Zwift.
            if 'zwift' in file_name_parts:
                return Keys.TYPE_VIRTUAL_CYCLING_KEY
            if 'rgt' in file_name_parts and 'cyclng' in file_name_parts:
                return Keys.TYPE_VIRTUAL_CYCLING_KEY
            return Keys.TYPE_CYCLING_KEY
        elif lower_activity_type == Keys.TYPE_OPEN_WATER_SWIMMING_KEY.lower():
            return Keys.TYPE_OPEN_WATER_SWIMMING_KEY
        elif lower_activity_type == Keys.TYPE_POOL_SWIMMING_KEY.lower():
            return Keys.TYPE_POOL_SWIMMING_KEY
        elif lower_activity_type == 'swimming' and sub_activity_type is not None:
            if lower_sub_activity_type == 'lap_swimming':
                return Keys.TYPE_POOL_SWIMMING_KEY
            return Keys.TYPE_OPEN_WATER_SWIMMING_KEY

        # Didn't match any known activity types, so take a guess from the name.
        if 'walk' in file_name_parts or 'walking' in file_name_parts:
            return Keys.TYPE_WALKING_KEY

        return Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY

    def import_gpx_file(self, username, user_id, file_name, desired_activity_id):
        """Imports the specified GPX file."""
        """Caller can request an activity ID by specifying a value to desired_activity_id."""

        # Sanity check.
        if not os.path.isfile(file_name):
            raise Exception("File does not exist.")

        # The GPX parser requires a file handle and not a file name.
        with open(file_name, 'r') as gpx_file:

            # Parse the file.
            gpx = gpxpy.parse(gpx_file)

            # Figure out the sport type.
            sport_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY
            if len(gpx.tracks) > 0:
                sport_type = Importer.normalize_activity_type(gpx.tracks[0].type, None, file_name)

            # Find the start timestamp.
            start_time_tuple = gpx.time.timetuple()
            start_time_unix = calendar.timegm(start_time_tuple)

            # Make sure this is not a duplicate activity.
            if self.activity_writer.is_duplicate_activity(user_id, start_time_unix, desired_activity_id):
                raise Exception("Duplicate activity.")

            # Indicate the start of the activity.
            device_str, activity_id = self.activity_writer.create_activity(username, user_id, gpx.name, gpx.description, sport_type, start_time_unix, desired_activity_id)

            # We'll store the most recent timecode here.
            end_time_unix = 0

            locations = []
            cadences = []
            heart_rate_readings = []
            power_readings = []
            temperature_readings = []

            for track in gpx.tracks:
                self.activity_writer.create_activity_track(device_str, activity_id, track.name, track.description)
                for segment in track.segments:
                    for point in segment.points:

                        # Read the timestamp. Discard any garbage by splitting after the (possible) plus sign.
                        dt_str = str(point.time).split('+')[0] + " UTC"
                        if dt_str.find('.') > 1:
                            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f %Z")
                        else:
                            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %Z")
                        dt_tuple = dt_obj.timetuple()
                        dt_unix = calendar.timegm(dt_tuple) * 1000

                        # Is this the most recent timestamp we've seen?
                        if dt_unix > end_time_unix:
                            end_time_unix = dt_unix

                        # Store the location.
                        location = []
                        location.append(dt_unix)
                        location.append(float(point.latitude))
                        location.append(float(point.longitude))
                        location.append(float(point.elevation))
                        locations.append(location)

                        # Look for other attributes.
                        extensions = point.extensions
                        if 'power' in extensions:
                            reading = []
                            reading.append(dt_unix)
                            reading.append(float(extensions['power']))
                            power_readings.append(reading)
                        if 'gpxtpx:TrackPointExtension' in extensions:
                            gpxtpx_extensions = extensions['gpxtpx:TrackPointExtension']
                            if 'gpxtpx:hr' in gpxtpx_extensions:
                                reading = []
                                reading.append(dt_unix)
                                reading.append(float(gpxtpx_extensions['gpxtpx:hr']))
                                heart_rate_readings.append(reading)
                            if 'gpxtpx:cad' in gpxtpx_extensions:
                                reading = []
                                reading.append(dt_unix)
                                reading.append(float(gpxtpx_extensions['gpxtpx:cad']))
                                cadences.append(reading)
                            if 'gpxtpx:atemp' in gpxtpx_extensions:
                                reading = []
                                reading.append(dt_unix)
                                reading.append(float(gpxtpx_extensions['gpxtpx:atemp']))
                                temperature_readings.append(reading)

            # Write all the locations at once.
            self.activity_writer.create_activity_locations(device_str, activity_id, locations)

            # Write all the sensor readings at once.
            self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_CADENCE_KEY, cadences)
            self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_HEART_RATE_KEY, heart_rate_readings)
            self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_POWER_KEY, power_readings)
            self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_TEMP_KEY, temperature_readings)

            # Let it be known that we are finished with this activity.
            self.activity_writer.finish_activity(activity_id, end_time_unix)
            return True, device_str, activity_id

        return False, "", ""

    def import_tcx_file(self, username, user_id, file_name, original_file_name, desired_activity_id):
        """Imports the specified TCX file."""
        """Caller can request an activity ID by specifying a value to desired_activity_id."""

        # Sanity check.
        if not os.path.isfile(file_name):
            raise Exception("File does not exist.")

        # Parse the file.
        tree = objectify.parse(file_name)
        if tree is None:
            raise Exception("Invalid TCX file (no tree node).")

        # Get the first node in the XML tree.
        root = tree.getroot()
        if root is None:
            raise Exception("Invalid TCX file (no root node).")

        # The interesting stuff starts with an activity.
        activity = root.Activities.Activity
        activity_type = activity.attrib['Sport']

        # Find the start timestamp.
        start_time_unix = 0
        if hasattr(activity, 'Id'):
            start_time_obj = datetime.datetime.strptime(str(activity.Id), "%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_tuple = start_time_obj.timetuple()
            start_time_unix = calendar.timegm(start_time_tuple)

        # Make sure this is not a duplicate activity.
        if self.activity_writer.is_duplicate_activity(user_id, start_time_unix, desired_activity_id):
            raise Exception("Duplicate activity.")

        # Since we don't have anything else, use the file name as the name of the activity.
        activity_name = os.path.splitext(os.path.basename(original_file_name))[0]

        # Figure out the type of the activity.
        normalized_activity_type = Importer.normalize_activity_type(activity_type, None, activity_name)

        # Indicate the start of the activity.
        device_str, activity_id = self.activity_writer.create_activity(username, user_id, activity_name, "", normalized_activity_type, start_time_unix, desired_activity_id)

        # We'll store the most recent timecode here.
        end_time_unix = 0

        locations = []
        cadences = []
        heart_rate_readings = []
        power_readings = []

        if hasattr(activity, 'Lap'):
            for lap in activity.Lap:
                if hasattr(lap, 'Track'):
                    for track in lap.Track:
                        if hasattr(track, 'Trackpoint'):
                            for point in track.Trackpoint:

                                # Read the timestamp.
                                dt_obj = datetime.datetime.strptime(str(point.Time), "%Y-%m-%dT%H:%M:%S.%fZ")
                                dt_tuple = dt_obj.timetuple()
                                dt_unix = calendar.timegm(dt_tuple) * 1000
                                dt_unix = dt_unix + dt_obj.microsecond / 1000

                                # Is this the most recent timestamp we've seen?
                                if dt_unix > end_time_unix:
                                    end_time_unix = dt_unix

                                # Store the location.
                                if hasattr(point, 'Position'):
                                    location = []
                                    location.append(dt_unix)
                                    location.append(float(point.Position.LatitudeDegrees))
                                    location.append(float(point.Position.LongitudeDegrees))
                                    if hasattr(point, 'AltitudeMeters'):
                                        location.append(float(point.AltitudeMeters))
                                    else:
                                        location.append(0.0)
                                    locations.append(location)

                                # Look for other attributes.
                                if hasattr(point, 'Cadence'):
                                    reading = []
                                    reading.append(dt_unix)
                                    reading.append(float(point.Cadence))
                                    cadences.append(reading)
                                if hasattr(point, 'HeartRateBpm'):
                                    reading = []
                                    reading.append(dt_unix)
                                    reading.append(float(point.HeartRateBpm.Value))
                                    heart_rate_readings.append(reading)
                                if hasattr(point, 'Extensions'):
                                    elements = point.Extensions
                                    children = elements.getchildren()
                                    if len(children) > 0:
                                        subelement = children[0]
                                        if hasattr(subelement, 'Watts'):
                                            reading = []
                                            reading.append(dt_unix)
                                            reading.append(float(subelement.Watts))
                                            power_readings.append(reading)

        # Write all the locations at once.
        self.activity_writer.create_activity_locations(device_str, activity_id, locations)

        # Write all the sensor readings at once.
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_CADENCE_KEY, cadences)
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_HEART_RATE_KEY, heart_rate_readings)
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_POWER_KEY, power_readings)

        # Let it be known that we are finished with this activity.
        self.activity_writer.finish_activity(activity_id, end_time_unix)
        return True, device_str, activity_id

    def import_fit_file(self, username, user_id, file_name, original_file_name, desired_activity_id):
        """Imports the specified FIT file."""
        """Caller can request an activity ID by specifying a value to desired_activity_id."""

        # Sanity check.
        if not os.path.isfile(file_name):
            raise Exception("File does not exist.")

        activity_type = ''
        sub_activity_type = ''

        start_time_unix = 0
        end_time_unix = 0

        locations = []
        cadences = []
        heart_rate_readings = []
        power_readings = []
        temperatures = []
        events = []

        fit_file = fitparse.FitFile(file_name, data_processor=fitparse.StandardUnitsDataProcessor())
        for message in fit_file.messages:

            if not hasattr(message, 'fields'):
                continue

            fields = message.fields

            message_data = {}
            for field in fields:
                message_data[field.name] = field.value

            if 'sport' in message_data:
                activity_type = message_data['sport']
            if 'sub_sport' in message_data:
                sub_activity_type = message_data['sub_sport']
            if 'timestamp' not in message_data:
                continue

            dt_obj = message_data['timestamp']
            dt_tuple = dt_obj.timetuple()
            dt_unix_seconds = calendar.timegm(dt_tuple)
            dt_unix = dt_unix_seconds * 1000

            # Update start and end times.
            if 'event_type' in message_data and message_data['event_type'] == 'start':
                start_time_unix = dt_unix_seconds
            end_time_unix = dt_unix_seconds

            # If the start has not been found yet, then continue.
            if start_time_unix == 0:
                continue

            # Look for location and sensor data.
            if 'position_long' in message_data and 'position_lat' in message_data and message_data['position_lat'] is not None and message_data['position_long'] is not None:
                location = []
                location.append(dt_unix)
                location.append(float(message_data['position_lat']))
                location.append(float(message_data['position_long']))
                if 'enhanced_altitude' in message_data:
                    location.append(float(message_data['enhanced_altitude']))
                locations.append(location)
            if 'cadence' in message_data and message_data['cadence'] is not None:
                reading = []
                reading.append(dt_unix)
                reading.append(float(message_data['cadence']))
                cadences.append(reading)
            if 'heart_rate' in message_data and message_data['heart_rate'] is not None:
                reading = []
                reading.append(dt_unix)
                reading.append(float(message_data['heart_rate']))
                heart_rate_readings.append(reading)
            if 'power' in message_data and message_data['power'] is not None:
                reading = []
                reading.append(dt_unix)
                reading.append(float(message_data['power']))
                power_readings.append(reading)
            if 'temperature' in message_data and message_data['temperature'] is not None:
                reading = []
                reading.append(dt_unix)
                reading.append(float(message_data['temperature']))
                temperatures.append(reading)
            if 'event' in message_data and message_data['event'] is not None:
                events.append(message_data)

        # Make sure this is not a duplicate activity.
        if self.activity_writer.is_duplicate_activity(user_id, start_time_unix, desired_activity_id):
            raise Exception("Duplicate activity.")

        # Since we don't have anything else, use the file name as the name of the activity.
        activity_name = os.path.splitext(os.path.basename(original_file_name))[0]

        # Figure out the type of the activity.
        normalized_activity_type = Importer.normalize_activity_type(activity_type, sub_activity_type, activity_name)

        # Indicate the start of the activity.
        device_str, activity_id = self.activity_writer.create_activity(username, user_id, activity_name, "", normalized_activity_type, start_time_unix, desired_activity_id)

        # Write all the locations at once.
        self.activity_writer.create_activity_locations(device_str, activity_id, locations)

        # Write all the sensor readings at once.
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_CADENCE_KEY, cadences)
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_HEART_RATE_KEY, heart_rate_readings)
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_POWER_KEY, power_readings)
        self.activity_writer.create_activity_sensor_readings(activity_id, Keys.APP_TEMP_KEY, temperatures)
        self.activity_writer.create_activity_events(activity_id, events)

        # Let it be known that we are finished with this activity.
        self.activity_writer.finish_activity(activity_id, end_time_unix)
        return True, device_str, activity_id

    def import_accelerometer_csv_file(self, username, user_id, file_name, desired_activity_id):
        """Imports a CSV file containing accelerometer data."""
        """Caller can request an activity ID by specifying a value to desired_activity_id."""

        # Sanity check.
        if not os.path.isfile(file_name):
            raise Exception("File does not exist.")

        end_time_unix = 0
        row_count = 0
        device_str = ""
        activity_id = ""

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:

                # Skip the header row.
                if row_count == 0:
                    row_count = row_count + 1
                    continue

                ts = float(row[0])
                x = float(row[1])
                y = float(row[2])
                z = float(row[3])
                accel_data = [ x, y, z ]

                # Is this the most recent timestamp we've seen?
                if ts > end_time_unix:
                    end_time_unix = ts

                # Indicate the start of the activity.
                if row_count == 1:
                    device_str, activity_id = self.activity_writer.create_activity(username, user_id, "", "", Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY, ts, desired_activity_id)

                self.activity_writer.create_activity_sensor_reading(activity_id, ts, Keys.APP_ACCELEROMETER_KEY, accel_data)
                row_count = row_count + 1

        # Let it be known that we are finished with this activity.
        self.activity_writer.finish_activity(activity_id, end_time_unix)
        return True, device_str, activity_id

    def import_activity_from_file(self, username, user_id, local_file_name, original_file_name, file_extension, desired_activity_id):
        """Imports the specified file, parsing it based on the provided extension."""
        """Result is {success, device_id, activity_id}."""
        """Caller can request an activity ID by specifying a value to desired_activity_id."""
        result = ( False, "", "" )
        try:
            if file_extension == '.gpx':
                result = self.import_gpx_file(username, user_id, local_file_name, desired_activity_id)
            elif file_extension == '.tcx':
                result = self.import_tcx_file(username, user_id, local_file_name, original_file_name, desired_activity_id)
            elif file_extension == '.fit':
                result = self.import_fit_file(username, user_id, local_file_name, original_file_name, desired_activity_id)
            elif file_extension == '.csv':
                result = self.import_accelerometer_csv_file(username, user_id, local_file_name, desired_activity_id)
        except:
            traceback.print_exc(file=sys.stdout)
            logger = logging.getLogger()
            logger.error(sys.exc_info()[0])
        return result
