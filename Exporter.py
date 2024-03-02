# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Michael J Simms
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
"""Writes CSV, GPX and TCX data."""

import inspect
import os
import sys

import Keys
import GpxWriter
import TcxWriter

# Locate and load the distance module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import distance

class Exporter(object):
    """Exporter for GPX and TCX data as well as CSV accelerometer data."""

    def __init__(self):
        super(Exporter, self).__init__()

    def nearest_sensor_reading(self, time_ms, current_reading, sensor_iter):
        try:
            if current_reading is None:
                current_reading = next(sensor_iter)
            else:
                sensor_time = float(list(current_reading.keys())[0])
                while sensor_time < time_ms:
                    current_reading = next(sensor_iter)
                    sensor_time = float(list(current_reading.keys())[0])
        except StopIteration:
            return None
        return current_reading

    def nearest_loc_reading(self, time_ms, current_reading, nearest_loc, loc_iter):
        try:
            if current_reading is None:
                current_reading = next(loc_iter)
            else:
                sensor_time = current_reading[Keys.APP_AXIS_TIME]
                while sensor_time < time_ms:
                    current_reading = next(loc_iter)
                    sensor_time = current_reading[Keys.APP_AXIS_TIME]
        except StopIteration:
            return None
        return nearest_loc

    def nearest_accel_reading(self, time_ms, current_reading, accel_iter):
        try:
            if current_reading is None:
                current_reading = next(accel_iter)
            else:
                sensor_time = current_reading[Keys.APP_AXIS_TIME]
                while sensor_time < time_ms:
                    current_reading = next(accel_iter)
                    sensor_time = current_reading[Keys.APP_AXIS_TIME]
        except StopIteration:
            return None
        return current_reading

    def export_as_csv(self, file_name, activity):
        """Formats the activity data as CSV."""
        accel_readings = []
        locations = []
        cadence_readings = []
        hr_readings = []
        temp_readings = []
        power_readings = []

        if Keys.APP_ACCELEROMETER_KEY in activity:
            accel_readings = activity[Keys.APP_ACCELEROMETER_KEY]
        if Keys.APP_LOCATIONS_KEY in activity:
            locations = activity[Keys.APP_LOCATIONS_KEY]
        if Keys.APP_CADENCE_KEY in activity:
            cadence_readings = activity[Keys.APP_CADENCE_KEY]
        if Keys.APP_HEART_RATE_KEY in activity:
            hr_readings = activity[Keys.APP_HEART_RATE_KEY]
        if Keys.APP_TEMP_KEY in activity:
            temp_readings = activity[Keys.APP_TEMP_KEY]
        if Keys.APP_POWER_KEY in activity:
            power_readings = activity[Keys.APP_POWER_KEY]

        accel_iter = iter(accel_readings)
        location_iter = iter(locations)
        cadence_iter = iter(cadence_readings)
        hr_iter = iter(hr_readings)
        temp_iter = iter(temp_readings)
        power_iter = iter(power_readings)

        nearest_accel = None
        nearest_loc = None
        nearest_cadence = None
        nearest_hr = None
        nearest_temp = None
        nearest_power = None

        buf = "time,latitude,longitude,altitude,cadence,hr,temp,power,x,y,z\r\n"
        done = False
        while not done:
            try:
                # Get the next location. If we have accelerometer data then we should key off of that
                # timestamp since those are typically sampled at sub-second intervals.
                if accel_readings:
                    nearest_accel = next(accel_iter)
                    current_time = nearest_accel[Keys.APP_AXIS_TIME]
                    nearest_loc = self.nearest_loc_reading(current_time, nearest_accel, nearest_loc, location_iter)
                else:
                    nearest_loc = next(location_iter)
                    current_time = nearest_loc[Keys.LOCATION_TIME_KEY]

                # Get the next sensor readings.
                nearest_cadence = self.nearest_sensor_reading(current_time, nearest_cadence, cadence_iter)
                nearest_hr = self.nearest_sensor_reading(current_time, nearest_hr, hr_iter)
                nearest_temp = self.nearest_sensor_reading(current_time, nearest_temp, temp_iter)
                nearest_power = self.nearest_sensor_reading(current_time, nearest_power, power_iter)

                # Write the next row.
                buf += str(current_time)
                buf += ","
                if nearest_loc:
                    buf += str(nearest_loc[Keys.LOCATION_LAT_KEY])
                    buf += ","
                    buf += str(nearest_loc[Keys.LOCATION_LON_KEY])
                    buf += ","
                    buf += str(nearest_loc[Keys.LOCATION_ALT_KEY])
                    buf += ","
                else:
                    buf += ",,,"
                if nearest_cadence:
                    buf += str(nearest_cadence)
                buf += ","
                if nearest_hr:
                    buf += str(nearest_hr)
                buf += ","
                if nearest_temp:
                    buf += str(nearest_temp)
                buf += ","
                if nearest_power:
                    buf += str(nearest_power)
                buf += ","
                if nearest_accel:
                    buf += str(nearest_accel[Keys.APP_AXIS_NAME_X])
                    buf += ","
                    buf += str(nearest_accel[Keys.APP_AXIS_NAME_Y])
                    buf += ","
                    buf += str(nearest_accel[Keys.APP_AXIS_NAME_Z])
                    buf += ","
                else:
                    buf += ",,,"
                buf += "\r\n"
            except StopIteration:
                done = True

        return buf

    def export_as_gpx(self, file_name, activity):
        """Exports the activity in GPX format."""
        locations = []
        cadence_readings = []
        hr_readings = []
        temp_readings = []
        power_readings = []

        if Keys.APP_LOCATIONS_KEY in activity:
            locations = activity[Keys.APP_LOCATIONS_KEY]
        if Keys.APP_CADENCE_KEY in activity:
            cadence_readings = activity[Keys.APP_CADENCE_KEY]
        if Keys.APP_HEART_RATE_KEY in activity:
            hr_readings = activity[Keys.APP_HEART_RATE_KEY]
        if Keys.APP_TEMP_KEY in activity:
            temp_readings = activity[Keys.APP_TEMP_KEY]
        if Keys.APP_POWER_KEY in activity:
            power_readings = activity[Keys.APP_POWER_KEY]

        location_iter = iter(locations)
        if len(locations) == 0:
            raise Exception("No locations for this activity.")

        cadence_iter = iter(cadence_readings)
        hr_iter = iter(hr_readings)
        temp_iter = iter(temp_readings)
        power_iter = iter(power_readings)

        nearest_cadence = None
        nearest_hr = None
        nearest_temp = None
        nearest_power = None

        writer = GpxWriter.GpxWriter()
        writer.create_gpx(file_name, "")

        start_time_ms = locations[0][Keys.LOCATION_TIME_KEY]
        writer.write_metadata(start_time_ms)

        writer.start_track()
        writer.write_type(activity[Keys.ACTIVITY_TYPE_KEY])
        writer.start_track_segment()

        done = False
        while not done:
            try:
                # Get the next location.
                current_location = next(location_iter)
                current_lat = current_location[Keys.LOCATION_LAT_KEY]
                current_lon = current_location[Keys.LOCATION_LON_KEY]
                current_alt = current_location[Keys.LOCATION_ALT_KEY]
                current_time = current_location[Keys.LOCATION_TIME_KEY]

                # Get the next sensor readings.
                nearest_cadence = self.nearest_sensor_reading(current_time, nearest_cadence, cadence_iter)
                nearest_hr = self.nearest_sensor_reading(current_time, nearest_hr, hr_iter)
                nearest_temp = self.nearest_sensor_reading(current_time, nearest_temp, temp_iter)
                nearest_power = self.nearest_sensor_reading(current_time, nearest_power, power_iter)

                # Write the next location.
                writer.start_trackpoint(current_lat, current_lon, current_alt, current_time)

                # Write any associated sensor readings.
                if nearest_cadence or nearest_hr:
                    writer.start_extensions()
                    writer.start_trackpoint_extensions()

                    if nearest_cadence is not None:
                        writer.store_cadence_rpm(list(nearest_cadence.values())[0])
                    if nearest_hr is not None:
                        writer.store_heart_rate_bpm(list(nearest_hr.values())[0])

                    writer.end_trackpoint_extensions()
                    writer.end_extensions()

                writer.end_trackpoint()
            except StopIteration:
                done = True

        writer.end_track_segment()
        writer.end_track()
        writer.close()

        result = writer.buffer()

        return result

    def export_as_tcx(self, file_name, activity):
        """Exports the activity in TCX format."""
        locations = []
        cadence_readings = []
        hr_readings = []
        temp_readings = []
        power_readings = []

        if Keys.APP_LOCATIONS_KEY in activity:
            locations = activity[Keys.APP_LOCATIONS_KEY]
        if Keys.APP_CADENCE_KEY in activity:
            cadence_readings = activity[Keys.APP_CADENCE_KEY]
        if Keys.APP_HEART_RATE_KEY in activity:
            hr_readings = activity[Keys.APP_HEART_RATE_KEY]
        if Keys.APP_TEMP_KEY in activity:
            temp_readings = activity[Keys.APP_TEMP_KEY]
        if Keys.APP_POWER_KEY in activity:
            power_readings = activity[Keys.APP_POWER_KEY]

        location_iter = iter(locations)
        if len(locations) == 0:
            raise Exception("No locations for this activity.")

        cadence_iter = iter(cadence_readings)
        hr_iter = iter(hr_readings)
        temp_iter = iter(temp_readings)
        power_iter = iter(power_readings)

        nearest_cadence = None
        nearest_hr = None
        nearest_temp = None
        nearest_power = None

        writer = TcxWriter.TcxWriter()
        writer.create_tcx(file_name)
        writer.start_activity(activity[Keys.ACTIVITY_TYPE_KEY])

        # Lap time
        lap_start_time_ms = locations[0][Keys.LOCATION_TIME_KEY]
        lap_end_time_ms = locations[-1][Keys.LOCATION_TIME_KEY]
        lap_time_sec = (lap_end_time_ms - lap_start_time_ms) / 1000

        # Lap distance
        lap_distance_meters = 0
        if Keys.ACTIVITY_SUMMARY_KEY in activity:
            summary_data = activity[Keys.ACTIVITY_SUMMARY_KEY]
            if summary_data:
                lap_distance_meters = summary_data[Keys.LONGEST_DISTANCE]

        # The lap ID is just the start time for the lap.
        writer.store_id(lap_start_time_ms / 1000)

        prev_location = None
        done = False
        while not done:

            writer.start_lap(lap_start_time_ms)
            writer.store_lap_seconds(lap_time_sec)
            writer.store_lap_distance(lap_distance_meters)
            writer.store_lap_calories(0)
            writer.start_track()

            while not done:

                try:
                    # Get the next location.
                    current_location = next(location_iter)
                    current_lat = current_location[Keys.LOCATION_LAT_KEY]
                    current_lon = current_location[Keys.LOCATION_LON_KEY]
                    current_alt = current_location[Keys.LOCATION_ALT_KEY]
                    current_time = current_location[Keys.LOCATION_TIME_KEY]

                    # Get the next sensor readings.
                    nearest_cadence = self.nearest_sensor_reading(current_time, nearest_cadence, cadence_iter)
                    nearest_hr = self.nearest_sensor_reading(current_time, nearest_hr, hr_iter)
                    nearest_temp = self.nearest_sensor_reading(current_time, nearest_temp, temp_iter)
                    nearest_power = self.nearest_sensor_reading(current_time, nearest_power, power_iter)

                    writer.start_trackpoint()
                    writer.store_time(current_time)
                    writer.store_position(current_lat, current_lon)
                    writer.store_altitude_meters(current_alt)

                    if prev_location is not None:
                        prev_lat = prev_location[Keys.LOCATION_LAT_KEY]
                        prev_lon = prev_location[Keys.LOCATION_LON_KEY]
                        prev_alt = prev_location[Keys.LOCATION_ALT_KEY]
                        meters_traveled = distance.haversine_distance(current_lat, current_lon, current_alt, prev_lat, prev_lon, prev_alt)
                        writer.store_distance_meters(meters_traveled)

                    if nearest_cadence is not None:
                        writer.store_cadence_rpm(list(nearest_cadence.values())[0])
                    if nearest_hr is not None:
                        writer.store_heart_rate_bpm(list(nearest_hr.values())[0])

                    if nearest_temp is not None or nearest_power is not None:
                        writer.start_trackpoint_extensions()
                        if nearest_temp is not None:
                            pass
                        if nearest_power is not None:
                            writer.store_power_in_watts(list(nearest_power.values())[0])
                        writer.end_trackpoint_extensions()

                    writer.end_trackpoint()

                    prev_location = current_location
                except StopIteration:
                    done = True

            writer.end_track()
            writer.end_lap()

        writer.end_activity()
        writer.close()

        result = writer.buffer()

        return result

    def export(self, activity, file_name, file_type):
        """Exports the activity in the specified format."""
        buf = ""
        if file_type == 'csv':
            buf = self.export_as_csv(file_name, activity)
        elif file_type == 'gpx':
            buf = self.export_as_gpx(file_name, activity)
        elif file_type == 'tcx':
            buf = self.export_as_tcx(file_name, activity)
        else:
            raise Exception("Invalid file type specified.")
        return buf
