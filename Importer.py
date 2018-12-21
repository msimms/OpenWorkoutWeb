# Copyright 2017 Michael J Simms
"""Parses GPX and TCX files, passing the contents to a ActivityWriter object."""

import calendar
import csv
import datetime
import gpxpy
import logging
import os
import traceback
import sys
from lxml import objectify

import Keys

class ActivityWriter(object):
    """Base class for any class that handles data read from the Importer."""

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time):
        """Pure virtual method for starting a location stream - creates the activity ID for the specified user."""
        pass

    def create_track(self, device_str, activity_id, track_name, track_description):
        """Pure virtual method for starting a location track - creates the activity ID for the specified user."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Pure virtual method for processing a location read by the importer."""
        pass

    def create_locations(self, device_str, activity_id, locations):
        """Pure virtual method for processing multiple location reads. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        pass

    def create_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Pure virtual method for processing a sensor reading from the importer."""
        pass

    def create_sensor_readings(self, activity_id, sensor_type, values):
        """Pure virtual method for processing multiple sensor readings. 'values' is an array of arrays in the form [time, value]."""
        pass

    def finish_activity(self):
        """Pure virtual method for any post-processing."""
        pass

class Importer(object):
    """Importer for GPX and TCX location files."""

    def __init__(self, activity_writer):
        super(Importer, self).__init__()
        self.activity_writer = activity_writer

    @staticmethod
    def normalize_activity_type(activity_type):
        """Takes the various activity names that appear in GPX and TCX files and normalizes to the ones used in this app."""
        if activity_type == 'Biking':
            activity_type = 'Cycling'
        elif len(activity_type) == 0:
            activity_type = 'Unknown'
        return activity_type

    def import_gpx_file(self, username, user_id, file_name):
        """Imports the specified GPX file."""

        # The GPX parser requires a file handle and not a file name.
        with open(file_name, 'r') as gpx_file:

            # Parse the file.
            gpx = gpxpy.parse(gpx_file)

            # Find the start timestamp.
            start_time_tuple = gpx.time.timetuple()
            start_time_unix = calendar.timegm(start_time_tuple)

            # Indicate the start of the activity.
            device_str, activity_id = self.activity_writer.create_activity(username, user_id, gpx.name, gpx.description, 'Unknown', start_time_unix)

            locations = []
            cadences = []
            heart_rate_readings = []
            power_readings = []
            temperature_readings = []

            for track in gpx.tracks:
                self.activity_writer.create_track(device_str, activity_id, track.name, track.description)
                for segment in track.segments:
                    for point in segment.points:

                        # Read the timestamp.
                        dt_str = str(point.time) + " UTC"
                        dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %Z")
                        dt_tuple = dt_obj.timetuple()
                        dt_unix = calendar.timegm(dt_tuple) * 1000

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
            self.activity_writer.create_locations(device_str, activity_id, locations)

            # Write all the sensor readings at once.
            self.activity_writer.create_sensor_readings(activity_id, Keys.APP_CADENCE_KEY, cadences)
            self.activity_writer.create_sensor_readings(activity_id, Keys.APP_HEART_RATE_KEY, heart_rate_readings)
            self.activity_writer.create_sensor_readings(activity_id, Keys.APP_POWER_KEY, power_readings)
            self.activity_writer.create_sensor_readings(activity_id, Keys.APP_TEMP_KEY, temperature_readings)

            # Let it be known that we are finished with this activity.
            self.activity_writer.finish_activity()
            return True, device_str, activity_id

        return False, "", ""

    def import_tcx_file(self, username, user_id, file_name, original_file_name):
        """Imports the specified TCX file."""

        # Parse the file.
        tree = objectify.parse(file_name)
        if tree is None:
            return False, "", ""

        # Get the first node in the XML tree.
        root = tree.getroot()
        if root is None:
            return False, "", ""

        # The interesting stuff starts with an activity.
        activity = root.Activities.Activity
        activity_type = activity.attrib['Sport']

        # Find the start timestamp.
        start_time_unix = 0
        if hasattr(activity, 'Id'):
            start_time_obj = datetime.datetime.strptime(str(activity.Id), "%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_tuple = start_time_obj.timetuple()
            start_time_unix = calendar.timegm(start_time_tuple)

        # Since we don't have anything else, use the file name as the name of the activity.
        activity_name = os.path.splitext(os.path.basename(original_file_name))[0]

        # Indicate the start of the activity.
        normalized_activity_type = Importer.normalize_activity_type(activity_type)
        device_str, activity_id = self.activity_writer.create_activity(username, user_id, activity_name, "", normalized_activity_type, start_time_unix)

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
        self.activity_writer.create_locations(device_str, activity_id, locations)

        # Write all the sensor readings at once.
        self.activity_writer.create_sensor_readings(activity_id, Keys.APP_CADENCE_KEY, cadences)
        self.activity_writer.create_sensor_readings(activity_id, Keys.APP_HEART_RATE_KEY, heart_rate_readings)
        self.activity_writer.create_sensor_readings(activity_id, Keys.APP_POWER_KEY, power_readings)

        # Let it be known that we are finished with this activity.
        self.activity_writer.finish_activity()
        return True, device_str, activity_id

    def import_accelerometer_csv_file(self, username, user_id, file_name):
        """Imports a CSV file containing accelerometer data."""

        columns = []
        ts_list = []
        x_list = []
        y_list = []
        z_list = []
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

                # Indicate the start of the activity.
                if row_count == 1:
                    device_str, activity_id = self.activity_writer.create_activity(username, user_id, "", "", "Lifting", ts)

                self.activity_writer.create_sensor_reading(activity_id, ts, Keys.APP_ACCELEROMETER_KEY, accel_data)
                row_count = row_count + 1

        # Let it be known that we are finished with this activity.
        self.activity_writer.finish_activity()
        return True, device_str, activity_id

    def import_file(self, username, user_id, local_file_name, original_file_name, file_extension):
        """Imports the specified file, parsing it based on the provided extension."""
        try:
            if file_extension == '.gpx':
                return self.import_gpx_file(username, user_id, local_file_name)
            elif file_extension == '.tcx':
                return self.import_tcx_file(username, user_id, local_file_name, original_file_name)
            elif file_extension == '.csv':
                return self.import_accelerometer_csv_file(username, user_id, local_file_name)
        except:
            traceback.print_exc(file=sys.stdout)
            logger = logging.getLogger()
            logger.error(sys.exc_info()[0])
        return False, "", ""
