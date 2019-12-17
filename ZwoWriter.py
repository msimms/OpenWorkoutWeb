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

import XmlWriter

ZWO_TAG_NAME_FILE = "workout_file"
ZWO_TAG_NAME_AUTHOR = "author"
ZWO_TAG_NAME_NAME = "name"
ZWO_TAG_NAME_DESCRIPTION = "description"
ZWO_TAG_NAME_SPORT_TIME = "sportType"
ZWO_TAG_NAME_WORKOUT = "workout"
ZWO_TAG_NAME_WORKOUT_WARMUP = "Warmup"
ZWO_TAG_NAME_WORKOUT_COOLDOWN = "Cooldown"
ZWO_TAG_NAME_WORKOUT_INTERVALS = "IntervalsT"
ZWO_TAG_NAME_WORKOUT_FREERIDE = "FreeRide"

class ZwoWriter(XmlWriter.XmlWriter):
    """Formats an ZWO file."""

    def __init__(self):
        XmlWriter.XmlWriter.__init__(self)

    def create_zwo(self, file_name):
        self.create(file_name)
        self.open_tag(ZWO_TAG_NAME_FILE)

    def close(self):
        self.close_all_tags()

    def store_author(self, author):
        if self.current_tag() is not ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the author.")
        self.write_tag_and_value(ZWO_TAG_NAME_AUTHOR, author)

    def store_name(self, name):
        if self.current_tag() is not ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the name.")
        self.write_tag_and_value(ZWO_TAG_NAME_NAME, name)

    def store_description(self, description):
        if self.current_tag() is not ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the description.")
        self.write_tag_and_value(ZWO_TAG_NAME_DESCRIPTION, description)

    def store_sport_type(self, sport_type):
        if self.current_tag() is not ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the sport type.")
        self.write_tag_and_value(ZWO_TAG_NAME_SPORT_TIME, sport_type)

    def start_workout(self):
        self.open_tag(ZWO_TAG_NAME_WORKOUT)

    def end_workout(self):
        if self.current_tag() is not ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        self.close_tag()

    def store_workout_warmup(self, duration, power_low, power_high, pace):
        if self.current_tag() is not ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes["Duration"] = duration
        attributes["PowerLow"] = power_low
        attributes["PowerHigh"] = power_high
        attributes["pace"] = pace
        self.open_tag_with_attributes(ZWO_TAG_NAME_WORKOUT_WARMUP, attributes, False)

    def store_workout_cooldown(self, duration, power_low, power_high, pace):
        if self.current_tag() is not ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes["Duration"] = duration
        attributes["PowerLow"] = power_low
        attributes["PowerHigh"] = power_high
        attributes["pace"] = pace
        self.open_tag_with_attributes(ZWO_TAG_NAME_WORKOUT_COOLDOWN, attributes, False)

    def store_workout_intervals(self, repeat, on_duration, off_duration, on_power, pace):
        if self.current_tag() is not ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes["Repeat"] = repeat
        attributes["OnDuration"] = on_duration
        attributes["OffDuration"] = off_duration
        attributes["OnPower"] = on_power
        attributes["pace"] = pace
        self.open_tag_with_attributes(ZWO_TAG_NAME_WORKOUT_INTERVALS, attributes, False)

    def store_workout_freeride(self, duration, flat_road):
        if self.current_tag() is not ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes["Duration"] = duration
        attributes["FlatRoad"] = flat_road
        self.open_tag_with_attributes(ZWO_TAG_NAME_WORKOUT_FREERIDE, attributes, False)
