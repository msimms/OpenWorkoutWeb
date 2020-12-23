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

import calendar
import datetime
import itertools
import os
import sys

class ActivityMerge(object):
    """Class for merging two activities."""

    start_time_unix = 0
    end_time_unix = 0
    locations = []
    heart_rate_readings = []
    power_readings = []
    cadence_readings = []
    temperature_readings = []

    def __init__(self):
        pass

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
