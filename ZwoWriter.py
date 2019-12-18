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

import inspect
import os
import sys
import XmlWriter

# Locate and load the ZwoTags module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
zworeaderdir = os.path.join(currentdir, 'ZwoReader')
sys.path.insert(0, zworeaderdir)
import ZwoTags

class ZwoWriter(XmlWriter.XmlWriter):
    """Formats an ZWO file."""

    def __init__(self):
        XmlWriter.XmlWriter.__init__(self)

    def create_zwo(self, file_name):
        self.create(file_name)
        self.open_tag(ZwoTags.ZWO_TAG_NAME_FILE)

    def close(self):
        self.close_all_tags()

    def store_author(self, author):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the author.")
        self.write_tag_and_value(ZwoTags.ZWO_TAG_NAME_AUTHOR, author)

    def store_name(self, name):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the name.")
        self.write_tag_and_value(ZwoTags.ZWO_TAG_NAME_NAME, name)

    def store_description(self, description):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the description.")
        self.write_tag_and_value(ZwoTags.ZWO_TAG_NAME_DESCRIPTION, description)

    def store_sport_type(self, sport_type):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_FILE:
            raise Exception("ZWO tag error when writing the sport type.")
        self.write_tag_and_value(ZwoTags.ZWO_TAG_NAME_SPORT_TIME, sport_type)

    def start_workout(self):
        self.open_tag(ZwoTags.ZWO_TAG_NAME_WORKOUT)

    def end_workout(self):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        self.close_tag()

    def store_workout_warmup(self, duration, power_low, power_high, pace):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes[ZwoTags.ZWO_ATTR_NAME_DURATION] = duration
        if power_low is not None:
            attributes[ZwoTags.ZWO_ATTR_NAME_POWERLOW] = power_low
        if power_high is not None:
            attributes[ZwoTags.ZWO_ATTR_NAME_POWERHIGH] = power_high
        if pace is not None:
            attributes[ZwoTags.ZWO_ATTRIBUTE_PACE] = pace
        self.open_tag_with_attributes(ZwoTags.ZWO_TAG_NAME_WORKOUT_WARMUP, attributes, False)
        self.close_tag()

    def store_workout_cooldown(self, duration, power_low, power_high, pace):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes[ZwoTags.ZWO_ATTR_NAME_DURATION] = duration
        if power_low is not None:
            attributes[ZwoTags.ZWO_ATTR_NAME_POWERLOW] = power_low
        if power_high is not None:
            attributes[ZwoTags.ZWO_ATTR_NAME_POWERHIGH] = power_high
        if pace is not None:
            attributes[ZwoTags.ZWO_ATTR_NAME_PACE] = pace
        self.open_tag_with_attributes(ZwoTags.ZWO_TAG_NAME_WORKOUT_COOLDOWN, attributes, False)
        self.close_tag()

    def store_workout_intervals(self, repeat, on_duration, off_duration, on_power, pace):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes[ZwoTags.ZWO_ATTR_NAME_REPEAT] = repeat
        attributes[ZwoTags.ZWO_ATTR_NAME_ONDURATION] = on_duration
        attributes[ZwoTags.ZWO_ATTR_NAME_OFFDURATION] = off_duration
        attributes[ZwoTags.ZWO_ATTR_NAME_ONPOWER] = on_power
        attributes[ZwoTags.ZWO_ATTR_NAME_PACE] = pace
        self.open_tag_with_attributes(ZwoTags.ZWO_TAG_NAME_WORKOUT_INTERVALS, attributes, False)
        self.close_tag()

    def store_workout_freeride(self, duration, flat_road):
        if self.current_tag() is not ZwoTags.ZWO_TAG_NAME_WORKOUT:
            raise Exception("ZWO tag error when ending a workout.")
        attributes = {}
        attributes[ZwoTags.ZWO_ATTR_NAME_DURATION] = duration
        attributes[ZwoTags.ZWO_ATTR_NAME_FLATROAD] = flat_road
        self.open_tag_with_attributes(ZwoTags.ZWO_TAG_NAME_WORKOUT_FREERIDE, attributes, False)
        self.close_tag()
