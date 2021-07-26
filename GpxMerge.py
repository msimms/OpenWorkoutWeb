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
import calendar
import datetime
import gpxpy
import os
import sys
import ActivityMerge
import GpxWriter

class GpxMerge(ActivityMerge.ActivityMerge):
    """Class for merging two GPX files."""

    # These will keep track of where we are in each file.
    track_index1 = 0
    track_index2 = 0
    segment_index1 = 0
    segment_index2 = 0
    point_index1 = 0
    point_index2 = 0

    def __init__(self):
        ActivityMerge.ActivityMerge.__init__(self)

    def read_file(self, file_name):
        """Extracts the data from the specified file."""

        # The GPX parser requires a file handle and not a file name.
        with open(file_name, 'r') as gpx_file:

            # Parse the file.
            gpx = gpxpy.parse(gpx_file)

            # Find the start timestamp.
            start_time_tuple = gpx.time.timetuple()
            temp_start_time_unix = calendar.timegm(start_time_tuple)
            if temp_start_time_unix > self.start_time_unix:
                self.start_time_unix = temp_start_time_unix

            # Loop through all the data points and store them.
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:

                        # Read the timestamp.
                        dt_str = str(point.time) + " UTC"
                        dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %Z")
                        dt_tuple = dt_obj.timetuple()
                        dt_unix = calendar.timegm(dt_tuple) * 1000

                        # Is this the most recent timestamp we've seen?
                        if dt_unix > self.end_time_unix:
                            self.end_time_unix = dt_unix

                        # Store the location.
                        location = []
                        location.append(dt_unix)
                        location.append(float(point.latitude))
                        location.append(float(point.longitude))
                        location.append(float(point.elevation))
                        self.locations.append(location)

                        # Look for other attributes.
                        extensions = point.extensions
                        if 'power' in extensions:
                            reading = []
                            reading.append(dt_unix)
                            reading.append(float(extensions['power']))
                            self.power_readings.append(reading)
                        if 'gpxtpx:TrackPointExtension' in extensions:
                            gpxtpx_extensions = extensions['gpxtpx:TrackPointExtension']
                            if 'gpxtpx:hr' in gpxtpx_extensions:
                                reading = []
                                reading.append(dt_unix)
                                reading.append(float(gpxtpx_extensions['gpxtpx:hr']))
                                self.heart_rate_readings.append(reading)
                            if 'gpxtpx:cad' in gpxtpx_extensions:
                                reading = []
                                reading.append(dt_unix)
                                reading.append(float(gpxtpx_extensions['gpxtpx:cad']))
                                self.cadence_readings.append(reading)
                            if 'gpxtpx:atemp' in gpxtpx_extensions:
                                reading = []
                                reading.append(dt_unix)
                                reading.append(float(gpxtpx_extensions['gpxtpx:atemp']))
                                self.temperature_readings.append(reading)

    def write_file(self, file_name):
        """Exports the merged data in GPX format."""

        location_iter = iter(self.locations)
        if len(self.locations) == 0:
            raise Exception("No locations for this activity.")

        cadence_iter = iter(self.cadence_readings)
        hr_iter = iter(self.heart_rate_readings)
        temp_iter = iter(self.temperature_readings)
        power_iter = iter(self.power_readings)

        nearest_cadence = None
        nearest_hr = None
        nearest_temp = None
        nearest_power = None

        writer = GpxWriter.GpxWriter()
        writer.create_gpx(file_name, "")

        start_time_ms = self.locations[0][0]
        writer.write_metadata(start_time_ms)

        writer.start_track()
        writer.start_track_segment()

        done = False
        while not done:

            try:
                # Get the next location.
                current_location = location_iter.next()
                current_time = current_location[0]
                current_lat = current_location[1]
                current_lon = current_location[2]
                current_alt = current_location[3]

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
                        writer.store_cadence_rpm(nearest_cadence.values()[0])
                    if nearest_hr is not None:
                        writer.store_heart_rate_bpm(nearest_hr.values()[0])

                    writer.end_trackpoint_extensions()
                    writer.end_extensions()

                writer.end_trackpoint()
            except StopIteration:
                done = True

        writer.end_track_segment()
        writer.end_track()
        writer.close()

        with open(file_name, "w") as f:
            f.write(writer.buffer())
            f.close()
        
    def merge_activities(self, file_name1, file_name2, outfile_name):
        """Main entry point for this class."""

        # Sanity check.
        if not os.path.isfile(file_name1):
            raise Exception("File does not exist.")
        if not os.path.isfile(file_name2):
            raise Exception("File does not exist.")

        # Read both files
        self.read_file(file_name1)
        self.read_file(file_name2)

        # Sort and merge the data.
        self.merge_all()

        # Write the merged file.
        if len(outfile_name) > 0:
            self.write_file(outfile_name)
        else:
            print(self.locations)


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

    merge_tool = GpxMerge()
    merge_tool.merge_activities(args.file1, args.file2, args.outfile)

if __name__ == "__main__":
    main()
