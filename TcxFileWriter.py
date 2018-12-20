# Copyright 2018 Michael J Simms

import datetime
import XmlFileWriter

class TcxFileWriter(XmlFileWriter.XmlFileWriter):
    """Formats an TCX file."""

    def __init__(self):
        XmlFileWriter.XmlFileWriter.__init__(self)

    def create_file(self, file_name):
        result = False

        if self.create_file(file_name):
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
            
            result = self.open_tag("TrainingCenterDatabase", attributes, True)
            result = result and self.open_tag(TCX_TAG_NAME_ACTIVITIES)

        return result

    def close_file(self):
        return self.close_all_tags()

    def write_id(self, start_time):
        buf = datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%dT%H:%M:%SZ')
        return self.write_tag_and_value(TCX_TAG_NAME_ID, buf)

    def start_activity(self, description):
        attributes = []
        attribute = {}
        attribute["Sport"] = description
        attributes.append(attribute)
        return self.open_tag(TCX_TAG_NAME_ACTIVITY, attributes)

    def end_activity(self):
        if self.current_tag is TCX_TAG_NAME_ACTIVITY:
            return self.close_tag()
        return False

    def start_lap(self):
        return self.open_tag(TCX_TAG_NAME_LAP)

    def start_lap(self, time_ms):
        attributes = []
        attribute = {}
        attribute["StartTime"] = self.format_time_ms(time_ms)
        attributes.push_back(attribute)
        return self.open_tag(TCX_TAG_NAME_LAP, attributes)

    def store_lap_seconds(self, time_ms):
        if self.current_tag is not TCX_TAG_NAME_LAP:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_TOTAL_TIME_SECONDS, time_ms / 1000)

    def store_lap_distance(self, distance_meters):
        if self.current_tag is not TCX_TAG_NAME_LAP:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_DISTANCE_METERS, distance_meters)

    def store_lap_max_speed(self, max_speed):
        if self.current_tag is not TCX_TAG_NAME_LAP:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_MAX_SPEED, max_speed)

    def store_lap_calories(self, calories):
        if self.current_tag is not TCX_TAG_NAME_LAP:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_CALORIES, calories)

    def end_lap(self):
        if self.current_tag is TCX_TAG_NAME_LAP:
            return self.close_tag()
        return False

    def start_track(self):
        return self.open_tag(TCX_TAG_NAME_TRACK)

    def end_track(self):
        if self.current_tag is TCX_TAG_NAME_TRACK:
            return self.close_tag()
        return False

    def start_trackpoint(self):
        return self.open_tag(TCX_TAG_NAME_TRACKPOINT)

    def store_time(self, time_ms):
        if self.current_tag is not TCX_TAG_NAME_TRACKPOINT != 0:
            return False
        time_str = self.format_time_ms(time_ms)
        return self.write_tag_and_value(TCX_TAG_NAME_TIME, time_str)

    def store_altitude_meters(self, altitude_meters):
        if self.current_tag is not TCX_TAG_NAME_TRACKPOINT:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_ALTITUDE_METERS, altitude_meters)

    def store_distance_meters(self, distance_meters):
        if self.current_tag is not TCX_TAG_NAME_TRACKPOINT:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_DISTANCE_METERS, distance_meters)

    def store_heart_rate_bpm(self, heart_rate_bpm):
        if self.current_tag is not TCX_TAG_NAME_TRACKPOINT:
            return False
        if not self.open_tag(TCX_TAG_NAME_HEART_RATE_BPM):
            return False
        if not self.write_tag_and_value(TCX_TAG_NAME_VALUE, heart_rate_bpm):
            return False
        return self.close_tag()

    def store_cadence_rpm(self, cadence_rpm):
        if self.current_tag is not TCX_TAG_NAME_TRACKPOINT:
            return False
        return self.write_tag_and_value(TCX_TAG_NAME_CADENCE, cadence_rpm)		

    def store_position(self, lat, lon):
        if self.current_tag is not TCX_TAG_NAME_TRACKPOINT:
            return False
        if self.open_tag(TCX_TAG_NAME_POSITION):
            self.write_tag_and_value(TCX_TAG_NAME_LATITUDE, lat)
            self.write_tag_and_value(TCX_TAG_NAME_LONGITUDE, lon)
            self.close_tag()
            return True
        return False

    def end_trackpoint(self):
        if self.current_tag is TCX_TAG_NAME_TRACKPOINT:
            return self.close_tag()
        return False

    def format_time_sec(self, t):
        buf = datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%dT%H:%M:%SZ')
        return buf

    def format_time_ms(self, t):
        sec  = t / 1000
        ms = t % 1000

        buf1 = datetime.datetime.utcfromtimestamp(sec).strftime('%Y-%m-%d %H:%M:%S')
        buf2 = buf1 + ".%04d" % ms
        return buf2
