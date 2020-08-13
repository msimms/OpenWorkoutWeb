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

class GpxMerge(object):
    """Class for merging two GPX files."""

    # These will keep track of where we are in each file.
    track_index1 = 0
    track_index2 = 0
    segment_index1 = 0
    segment_index2 = 0
    point_index1 = 0
    point_index2 = 0

    def __init__(self):
        pass

    def next_points(self, gpx1, gpx2):
        point1 = None
        point2 = None
        next_point = None

        # Find the next point from the first file.
        if self.track_index1 < len(gpx1.tracks):
            if self.segment_index1 < len(gpx1.tracks[self.track_index1].segments):
                if self.point_index1 < len(gpx1.tracks[self.track_index1].segments[self.segment_index1].points):
                    point1 = gpx1.tracks[self.track_index1].segments[self.segment_index1].points[self.point_index1]

        # Find the next point from the second file.
        if self.track_index2 < len(gpx2.tracks):
            if self.segment_index2 < len(gpx2.tracks[self.track_index2].segments):
                if self.point_index2 < len(gpx2.tracks[self.track_index2].segments[self.segment_index2].points):
                    point2 = gpx2.tracks[self.track_index2].segments[self.segment_index2].points[self.point_index2]

        print(point1)
        print(point2)
        return next_point

    def merge_gpx_files(self, file_name1, file_name2):
        # Sanity check.
        if not os.path.isfile(file_name1):
            raise Exception("File does not exist.")
        if not os.path.isfile(file_name2):
            raise Exception("File does not exist.")

        # The GPX parser requires a file handle and not a file name.
        with open(file_name1, 'r') as gpx_file1:
            with open(file_name2, 'r') as gpx_file2:

                # Parse the files.
                gpx1 = gpxpy.parse(gpx_file1)
                gpx2 = gpxpy.parse(gpx_file2)

                # Find the start timestamps.
                start_time_tuple1 = gpx1.time.timetuple()
                start_time_unix1 = calendar.timegm(start_time_tuple1)
                start_time_tuple2 = gpx2.time.timetuple()
                start_time_unix2 = calendar.timegm(start_time_tuple2)

                # Loop through all the data points in both files.
                done = False
                while not done:

                    # Find the next point, from whichever file it should come from.
                    point = self.next_points(gpx1, gpx2)
                    done = point is None


def main():
    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--file1", default="", help="One of the files to merge", required=True)
    parser.add_argument("--file2", default="", help="The other file to merge", required=True)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    merge_tool = GpxMerge()
    merge_tool.merge_gpx_files(args.file1, args.file2)

if __name__ == "__main__":
    main()
