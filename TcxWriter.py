# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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

import datetime
import XmlWriter

TCX_TAG_NAME_ACTIVITIES = "Activities"
TCX_TAG_NAME_ACTIVITY = "Activity"
TCX_TAG_NAME_LAP = "Lap"
TCX_TAG_NAME_TRACK = "Track"
TCX_TAG_NAME_TRACKPOINT = "Trackpoint"
TCX_TAG_NAME_TRACKPOINT_EXTENSIONS = "Extensions"
TCX_TAG_NAME_TIME = "Time"
TCX_TAG_NAME_ALTITUDE_METERS = "AltitudeMeters"
TCX_TAG_NAME_DISTANCE_METERS = "DistanceMeters"
TCX_TAG_NAME_HEART_RATE_BPM = "HeartRateBpm"
TCX_TAG_NAME_CADENCE = "Cadence"
TCX_TAG_NAME_POWER = "Watts"
TCX_TAG_NAME_POSITION = "Position"
TCX_TAG_NAME_LATITUDE = "LatitudeDegrees"
TCX_TAG_NAME_LONGITUDE = "LongitudeDegrees"
TCX_TAG_NAME_TOTAL_TIME_SECONDS = "TotalTimeSeconds"
TCX_TAG_NAME_MAX_SPEED = "MaximumSpeed"
TCX_TAG_NAME_CALORIES = "Calories"
TCX_TAG_NAME_ID = "Id"
TCX_TAG_NAME_VALUE = "Value"
TCX_TAG_NAME = "TCX"

class TcxWriter(XmlWriter.XmlWriter):
    """Formats an TCX file."""

    def __init__(self):
        XmlWriter.XmlWriter.__init__(self)

    def create_tcx_file(self, file_name):
        self.create_file(file_name)

        attributes = []

        attribute = {}
        attribute["xmlns"] = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
        attributes.append(attribute)

        attribute = {}
        attribute["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"
        attributes.append(attribute)
        
        attribute = {}
        attribute["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        attributes.append(attribute)
        
        attribute = {}
        attribute["xmlns:tc2"] = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
        attributes.append(attribute)

        attribute = {}
        attribute["targetNamespace"] = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
        attributes.append(attribute)

        attribute = {}
        attribute["elementFormDefault"] = "qualified"
        attributes.append(attribute)
        
        self.open_tag_with_attributes("TrainingCenterDatabase", attributes, True)
        self.open_tag(TCX_TAG_NAME_ACTIVITIES)

    def close_file(self):
        self.close_all_tags()

    def write_id(self, start_time):
        buf = datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.write_tag_and_value(TCX_TAG_NAME_ID, buf)

    def start_activity(self, description):
        attributes = []
        attribute = {}
        attribute["Sport"] = description
        attributes.append(attribute)
        self.open_tag_with_attributes(TCX_TAG_NAME_ACTIVITY, attributes, False)

    def end_activity(self):
        if self.current_tag() is TCX_TAG_NAME_ACTIVITY:
            self.close_tag()

    def start_lap(self, time_ms):
        attributes = []
        attribute = {}
        attribute["StartTime"] = self.format_time_ms(time_ms)
        attributes.append(attribute)
        self.open_tag_with_attributes(TCX_TAG_NAME_LAP, attributes, False)

    def store_lap_seconds(self, time_ms):
        if self.current_tag() is not TCX_TAG_NAME_LAP:
            raise Exception("TCX tag error when writing lap seconds.")
        self.write_tag_and_value(TCX_TAG_NAME_TOTAL_TIME_SECONDS, time_ms / 1000)

    def store_lap_distance(self, distance_meters):
        if self.current_tag() is not TCX_TAG_NAME_LAP:
            raise Exception("TCX tag error when writing lap distance.")
        self.write_tag_and_value(TCX_TAG_NAME_DISTANCE_METERS, distance_meters)

    def store_lap_max_speed(self, max_speed):
        if self.current_tag() is not TCX_TAG_NAME_LAP:
            raise Exception("TCX tag error when writing maximum lap speed.")
        self.write_tag_and_value(TCX_TAG_NAME_MAX_SPEED, max_speed)

    def store_lap_calories(self, calories):
        if self.current_tag() is not TCX_TAG_NAME_LAP:
            raise Exception("TCX tag error when writing lap calories.")
        self.write_tag_and_value(TCX_TAG_NAME_CALORIES, calories)

    def end_lap(self):
        if self.current_tag() is TCX_TAG_NAME_LAP:
            self.close_tag()

    def start_track(self):
        self.open_tag(TCX_TAG_NAME_TRACK)

    def end_track(self):
        if self.current_tag() is not TCX_TAG_NAME_TRACK:
            raise Exception("TCX tag error when ending a track.")

    def start_trackpoint(self):
        self.open_tag(TCX_TAG_NAME_TRACKPOINT)

    def end_trackpoint(self):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when ending a trackpoint.")
        self.close_tag()

    def start_trackpoint_extensions(self):
        self.open_tag(TCX_TAG_NAME_TRACKPOINT_EXTENSIONS)
        attributes = []
        attribute = {}
        attribute["xmlns"] = "http://www.garmin.com/xmlschemas/ActivityExtension/v2"
        attributes.append(attribute)
        self.open_tag_with_attributes(TCX_TAG_NAME, attributes, False)

    def end_trackpoint_extensions(self):
        if self.current_tag() is not TCX_TAG_NAME:
            raise Exception("TCX tag error when ending a trackpoint extension.")
        self.close_tag()
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT_EXTENSIONS:
            raise Exception("TCX tag error when ending a trackpoint extension.")
        self.close_tag()

    def store_time(self, time_ms):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when writing the time.")
        time_str = self.format_time_ms(time_ms)
        self.write_tag_and_value(TCX_TAG_NAME_TIME, time_str)

    def store_altitude_meters(self, altitude_meters):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when writing altitude data.")
        self.write_tag_and_value(TCX_TAG_NAME_ALTITUDE_METERS, altitude_meters)

    def store_distance_meters(self, distance_meters):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when writing distance data.")
        self.write_tag_and_value(TCX_TAG_NAME_DISTANCE_METERS, distance_meters)

    def store_heart_rate_bpm(self, heart_rate_bpm):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when writing heart rate data.")
        self.open_tag(TCX_TAG_NAME_HEART_RATE_BPM)
        self.write_tag_and_value(TCX_TAG_NAME_VALUE, heart_rate_bpm)
        self.close_tag()

    def store_cadence_rpm(self, cadence_rpm):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when writing cadence data.")
        self.write_tag_and_value(TCX_TAG_NAME_CADENCE, cadence_rpm)		

    def store_power_in_watts(self, power_watts):
        if self.current_tag() is not TCX_TAG_NAME:
            raise Exception("TCX tag error when writing power data.")
        self.write_tag_and_value(TCX_TAG_NAME_POWER, power_watts)		

    def store_position(self, lat, lon):
        if self.current_tag() is not TCX_TAG_NAME_TRACKPOINT:
            raise Exception("TCX tag error when writing position.")
        self.open_tag(TCX_TAG_NAME_POSITION)
        self.write_tag_and_value(TCX_TAG_NAME_LATITUDE, lat)
        self.write_tag_and_value(TCX_TAG_NAME_LONGITUDE, lon)
        self.close_tag()

    def format_time_sec(self, t):
        return datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%dT%H:%M:%SZ')

    def format_time_ms(self, t):
        sec  = t / 1000
        ms = t % 1000

        buf1 = datetime.datetime.utcfromtimestamp(sec).strftime('%Y-%m-%d %H:%M:%S')
        buf2 = buf1 + ".%04d" % ms
        return buf2
