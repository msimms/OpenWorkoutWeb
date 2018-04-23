# Copyright 2017 Michael J Simms
"""Parses GPX and TCX files, passing the contents to a LocationWriter object."""

import calendar
import datetime
import gpxpy
import tcxparser

import StraenKeys

class LocationWriter(object):
    """Base class for any class that handles data read from the Importer."""

    def create(self, username, stream_name, stream_description, activity_type):
        """Pure virtual method for starting a location stream - creates the activity ID for the specified user."""
        pass

    def create_track(self, device_str, activity_id, track_name, track_description):
        """Pure virtual method for starting a location track - creates the activity ID for the specified user."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Pure virtual method for processing a location read by the importer."""
        pass

    def create_sensor_reading(self, device_str, activity_id, date_time, key, value):
        """Pure virtual method for processing a sensor reading from the importer."""
        pass

class Importer(object):
    """Importer for GPX and TCX location files."""

    def __init__(self, location_store):
        super(Importer, self).__init__()
        self.location_writer = location_store

    def import_gpx_file(self, username, file_name):
        """Imports the specified GPX file."""
        with open(file_name, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            device_str, activity_id = self.location_writer.create(username, gpx.name, gpx.description, "")

            for track in gpx.tracks:
                self.location_writer.create_track(device_str, activity_id, track.name, track.description)
                for segment in track.segments:
                    for point in segment.points:
                        dt_str = str(point.time) + " UTC"
                        dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %Z").timetuple()
                        dt_unix = calendar.timegm(dt_obj)
                        self.location_writer.create_location(device_str, activity_id, dt_unix, point.latitude, point.longitude, point.elevation)

                        extensions = point.extensions
                        if 'power' in extensions:
                            self.location_writer.create_sensor_reading(device_str, activity_id, dt_unix, StraenKeys.POWER_KEY, extensions['power'])
                        if 'gpxtpx:TrackPointExtension' in extensions:
                            gpxtpx_extensions = extensions['gpxtpx:TrackPointExtension']
                            if 'gpxtpx:hr' in gpxtpx_extensions:
                                self.location_writer.create_sensor_reading(device_str, activity_id, dt_unix, StraenKeys.HEART_RATE_KEY, gpxtpx_extensions['gpxtpx:hr'])

            return True
        return False

    def import_tcx_file(self, username, file_name):
        """Imports the specified TCX file."""
        tcx = tcxparser.TCXParser(file_name)
        if tcx is not None:
            device_str, activity_id = self.location_writer.create(username, "", "", tcx.activity_type)

            for activity in tcx.activity:
                for lap in activity.Lap:
                    for track in lap.Track:
                        for point in track.Trackpoint:
                            dt_obj = datetime.datetime.strptime(str(point.Time), "%Y-%m-%dT%H:%M:%S.%fZ").timetuple()
                            dt_unix = calendar.timegm(dt_obj)
                            self.location_writer.create_location(device_str, activity_id, dt_unix, point.Position.LatitudeDegrees, point.Position.LongitudeDegrees, point.AltitudeMeters)
            return True
        return False

    def import_file(self, username, local_file_name, file_extension):
        """Imports the specified file, parsing it based on the provided extension."""
        try:
            if file_extension == '.gpx':
                return self.import_gpx_file(username, local_file_name)
            elif file_extension == '.tcx':
                return self.import_tcx_file(username, local_file_name)
        except:
            pass
        return False
