#! /usr/bin/env python

# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Mike Simms
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

import argparse
import os
import sys
import Exporter
import Importer
import Keys


class ActivityWriterForMerging(Importer.ActivityWriter):
    """Base class for any class that handles data read from the Importer."""

    activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY
    locations = []
    heart_rate_readings = []
    power_readings = []
    cadence_readings = []
    temperature_readings = []

    def __init__(self):
        super(Importer.ActivityWriter, self).__init__()

    def is_duplicate_activity(self, user_id, start_time, optional_activity_id):
        """Inherited from ActivityWriter. Returns TRUE if the activity appears to be a duplicate of another activity. Returns FALSE otherwise."""
        return False

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time, desired_activity_id):
        """Pure virtual method for starting a location stream - creates the activity ID for the specified user."""
        self.activity_type = activity_type
        return "", desired_activity_id

    def create_activity_track(self, device_str, activity_id, track_name, track_description):
        """Pure virtual method for starting a location track - creates the activity ID for the specified user."""
        pass

    def create_activity_locations(self, device_str, activity_id, locations):
        """Pure virtual method for processing multiple location reads. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        self.locations += locations

    def create_activity_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Pure virtual method for processing a sensor reading from the importer."""
        if sensor_type == Keys.APP_CADENCE_KEY:
            self.cadence_readings.append(value)
        elif sensor_type == Keys.APP_HEART_RATE_KEY:
            self.heart_rate_readings.append(value)
        elif sensor_type == Keys.APP_POWER_KEY:
            self.power_readings.append(value)
        elif sensor_type == Keys.APP_TEMP_KEY:
            self.temperature_readings.append(value)

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

class MergeTool(object):
    """Class for merging two GPX files."""

    locations = []
    heart_rate_readings = []
    power_readings = []
    cadence_readings = []
    temperature_readings = []

    def __init__(self):
        super(MergeTool, self).__init__()

    def sort(self, unsorted_list):
        new_list = sorted(unsorted_list, key=lambda k: k[0]) 
        return new_list

    def merge(self, unmerged_list):
        new_list = []
        prev_item = None
        for curr_item in unmerged_list:

            # If this item and the previous item have the same timestamp then we need to merge them.
            if prev_item and prev_item[0] == curr_item[0]:
                new_item = []
                for a,b in zip(prev_item, curr_item):
                    new_item.append((a+b)/2)

                # Replace the last item in the list with the newly computed item.
                new_list.pop()
                new_list.append(new_item)
                prev_item = new_item
            else:
                new_list.append(curr_item)
                prev_item = curr_item

        return new_list

    def nearest_sensor_reading(self, time_ms, current_reading, sensor_iter):
        try:
            if current_reading is None:
                current_reading = sensor_iter.next()
            else:
                sensor_time = float(current_reading.keys()[0])
                while sensor_time < time_ms:
                    current_reading = sensor_iter.next()
                    sensor_time = float(current_reading.keys()[0])
        except StopIteration:
            return None
        return current_reading

    def location_database_format_to_list(self, locations):
        result = []
        for location in locations:
            result.append([ location[Keys.LOCATION_TIME_KEY], location[Keys.LOCATION_LAT_KEY], location[Keys.LOCATION_LON_KEY], location[Keys.LOCATION_ALT_KEY] ])
        return result

    def sensor_database_format_to_list(self, readings):
        result = []
        for reading in readings:
            reading_time = list(reading.keys())[0]
            result.append([ reading_time, reading[reading_time] ])
        return result

    def locations_list_to_database_format(self, locations):
        result = []
        for location in locations:
            temp = {}
            temp[Keys.LOCATION_TIME_KEY] = location[0]
            temp[Keys.LOCATION_LAT_KEY] = location[1]
            temp[Keys.LOCATION_LON_KEY] = location[2]
            temp[Keys.LOCATION_ALT_KEY] = location[3]
            result.append(temp)
        return result

    def sensor_list_to_database_format(self, readings):
        result = []
        for reading in readings:
            reading_time = reading[0]
            temp = {}
            temp[reading_time] = reading[1]
            result.append(temp)
        return result

    def merge_all(self):
        """To be called after the files have been read."""

        # Sort everything.
        self.locations = self.sort(self.locations)
        self.heart_rate_readings = self.sort(self.heart_rate_readings)
        self.power_readings = self.sort(self.power_readings)
        self.cadence_readings = self.sort(self.cadence_readings)
        self.temperature_readings = self.sort(self.temperature_readings)

        # Merge everything, i.e. remove duplicates, etc.
        self.locations = self.merge(self.locations)
        self.heart_rate_readings = self.merge(self.heart_rate_readings)
        self.power_readings = self.merge(self.power_readings)
        self.cadence_readings = self.merge(self.cadence_readings)
        self.temperature_readings = self.merge(self.temperature_readings)

    def merge_activity_files(self, file_name1, file_name2, outfile_name):
        """Main entry point for this class."""

        # Sanity check.
        if not os.path.isfile(file_name1):
            raise Exception("File does not exist.")
        if not os.path.isfile(file_name2):
            raise Exception("File does not exist.")

        # Read the first file.
        extension1 = os.path.splitext(file_name1)[1]
        writer1 = ActivityWriterForMerging()
        importer1 = Importer.Importer(writer1)
        importer1.import_activity_from_file("", 0, file_name1, file_name1, extension1, 0)

        # Read the second file.
        extension2 = os.path.splitext(file_name1)[1]
        writer2 = ActivityWriterForMerging()
        importer2 = Importer.Importer(writer2)
        importer2.import_activity_from_file("", 0, file_name2, file_name2, extension2, 0)

        # Concatenate the first file's data to the second file's data.
        self.locations = writer1.locations + writer2.locations
        self.heart_rate_readings = writer1.heart_rate_readings + writer2.heart_rate_readings
        self.power_readings = writer1.power_readings + writer2.power_readings
        self.cadence_readings = writer1.cadence_readings + writer2.cadence_readings
        self.temperature_readings = writer1.temperature_readings + writer2.temperature_readings

        # Sort and merge the data.
        self.merge_all()

        # Put all the data into a dictionary.
        activity = {}
        activity[Keys.ACTIVITY_TYPE_KEY] = writer1.activity_type
        activity[Keys.APP_LOCATIONS_KEY] = self.locations_list_to_database_format(self.locations)
        activity[Keys.APP_HEART_RATE_KEY] = self.sensor_list_to_database_format(self.heart_rate_readings)
        activity[Keys.APP_POWER_KEY] = self.sensor_list_to_database_format(self.power_readings)
        activity[Keys.APP_CADENCE_KEY] = self.sensor_list_to_database_format(self.cadence_readings)
        activity[Keys.APP_TEMP_KEY] = self.sensor_list_to_database_format(self.temperature_readings)

        # Write the merged file.
        exporter = Exporter.Exporter()
        out_data = exporter.export(activity, None, extension1[1:])
        return out_data

    def merge_activities(self, activities):
        
        activity_id = ""
        activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY
        activity_time = None
        name = ""
        description = ""
        device_str = ""
        visibility = Keys.ACTIVITY_VISIBILITY_PRIVATE

        for activity in activities:

            # Has the activity ID been set?
            if Keys.ACTIVITY_ID_KEY in activity and len(activity_id) == 0:
                activity_id = activity[Keys.ACTIVITY_ID_KEY]

            # Has the activity type been set?
            if Keys.ACTIVITY_TYPE_KEY in activity and activity_type == Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY:
                activity_type = activity[Keys.ACTIVITY_TYPE_KEY]

            # Has the activity time been set?
            if Keys.ACTIVITY_START_TIME_KEY in activity:
                temp = activity[Keys.ACTIVITY_START_TIME_KEY]
                if activity_time is None or temp < activity[Keys.ACTIVITY_START_TIME_KEY]:
                    activity_time = temp

            # Has the name been set?
            if Keys.ACTIVITY_NAME_KEY in activity and len(name) == 0:
                name = activity[Keys.ACTIVITY_NAME_KEY]

            # Has the description been set?
            if Keys.ACTIVITY_DESCRIPTION_KEY in activity and len(description) == 0:
                description = activity[Keys.ACTIVITY_DESCRIPTION_KEY]

            # Has the device been set?
            if Keys.ACTIVITY_DEVICE_STR_KEY in activity and len(device_str) == 0:
                device_str = activity[Keys.ACTIVITY_DEVICE_STR_KEY]

            # Concatenate the data to any previous data that was read.
            if Keys.APP_LOCATIONS_KEY in activity:
                self.locations += self.location_database_format_to_list(activity[Keys.APP_LOCATIONS_KEY])
            if Keys.APP_HEART_RATE_KEY in activity:
                self.heart_rate_readings += self.sensor_database_format_to_list(activity[Keys.APP_HEART_RATE_KEY])
            if Keys.APP_POWER_KEY in activity:
                self.power_readings += self.sensor_database_format_to_list(activity[Keys.APP_POWER_KEY])
            if Keys.APP_CADENCE_KEY in activity:
                self.cadence_readings += self.sensor_database_format_to_list(activity[Keys.APP_CADENCE_KEY])
            if Keys.APP_TEMP_KEY in activity:
                self.temperature_readings += self.sensor_database_format_to_list(activity[Keys.APP_TEMP_KEY])

        # Sort and merge the data.
        self.merge_all()

        # Put all the data into a dictionary.
        activity = {}
        activity[Keys.ACTIVITY_ID_KEY] = activity_id
        activity[Keys.ACTIVITY_TYPE_KEY] = activity_type
        activity[Keys.ACTIVITY_START_TIME_KEY] = activity_time
        activity[Keys.ACTIVITY_NAME_KEY] = name
        activity[Keys.ACTIVITY_DESCRIPTION_KEY] = description
        activity[Keys.ACTIVITY_DEVICE_STR_KEY] = device_str
        activity[Keys.ACTIVITY_VISIBILITY_KEY] = visibility
        activity[Keys.APP_LOCATIONS_KEY] = self.locations_list_to_database_format(self.locations)
        activity[Keys.APP_HEART_RATE_KEY] = self.sensor_list_to_database_format(self.heart_rate_readings)
        activity[Keys.APP_POWER_KEY] = self.sensor_list_to_database_format(self.power_readings)
        activity[Keys.APP_CADENCE_KEY] = self.sensor_list_to_database_format(self.cadence_readings)
        activity[Keys.APP_TEMP_KEY] = self.sensor_list_to_database_format(self.temperature_readings)
        return activity

def main():
    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--file1", default="", help="One of the files to merge", required=True)
    parser.add_argument("--file2", default="", help="The other file to merge", required=True)
    parser.add_argument("--outfile", default="", help="The file", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    merge_tool = MergeTool()
    data = merge_tool.merge_activity_files(args.file1, args.file2, args.outfile)

    if len(args.outfile) > 0:
        f = open(args.outfile, "wt")
        f.write(data)
        f.close()

if __name__ == "__main__":
    main()
