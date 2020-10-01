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
"""Describes a workout to be performed."""

from __future__ import print_function
import datetime
import json
import inspect
import os
import sys
import time
import uuid
import IcsWriter
import Keys
import TrainingStressCalculator
import Units
import UserMgr
import ZwoWriter

# Locate and load the ZwoTags module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
zworeaderdir = os.path.join(currentdir, 'ZwoReader')
sys.path.insert(0, zworeaderdir)
import ZwoTags

class Workout(object):
    """Class that describes a workout to be performed."""

    def __init__(self, user_id):
        self.type = ""
        self.user_id = user_id
        self.sport_type = ""
        self.scheduled_time = None # The time at which this workout is to be performed
        self.warmup = {} # The warmup interval
        self.cooldown = {} # The cooldown interval
        self.intervals = [] # The workout intervals
        self.estimated_training_stress = None # Estimated training stress, the highter, the more stresful
        self.workout_id = uuid.uuid4() # Unique identifier for the workout

    def __getitem__(self, key):
        if key == Keys.WORKOUT_ID_KEY:
            return self.workout_id
        if key == Keys.WORKOUT_TYPE_KEY:
            return self.type
        if key == Keys.WORKOUT_SPORT_TYPE_KEY:
            return self.sport_type
        if key == Keys.WORKOUT_WARMUP_KEY:
            return self.warmup
        if key == Keys.WORKOUT_COOLDOWN_KEY:
            return self.cooldown
        if key == Keys.WORKOUT_INTERVALS_KEY:
            return self.intervals
        if key == Keys.WORKOUT_SCHEDULED_TIME_KEY and self.scheduled_time is not None:
            dt = time.mktime(self.scheduled_time.timetuple())
            return datetime.datetime(dt.year, dt.month, dt.day)
        if key == Keys.WORKOUT_ESTIMATED_STRESS_KEY:
            return self.estimated_training_stress
        return None

    def to_dict(self):
        """Converts the object representation to a dictionary, only converting what is actually useful, as opposed to __dict__."""
        output = {}
        output[Keys.WORKOUT_ID_KEY] = self.workout_id
        output[Keys.WORKOUT_TYPE_KEY] = self.type
        output[Keys.WORKOUT_SPORT_TYPE_KEY] = self.sport_type
        output[Keys.WORKOUT_WARMUP_KEY] = self.warmup
        output[Keys.WORKOUT_COOLDOWN_KEY] = self.cooldown
        output[Keys.WORKOUT_INTERVALS_KEY] = self.intervals
        if self.scheduled_time is not None:
            output[Keys.WORKOUT_SCHEDULED_TIME_KEY] = time.mktime(self.scheduled_time.timetuple())
        if self.estimated_training_stress is not None:
            output[Keys.WORKOUT_ESTIMATED_STRESS_KEY] = self.estimated_training_stress
        return output

    def from_dict(self, input):
        """Sets the object's members from a dictionary."""
        if Keys.WORKOUT_ID_KEY in input:
            self.workout_id = input[Keys.WORKOUT_ID_KEY]
        if Keys.WORKOUT_TYPE_KEY in input:
            self.type = input[Keys.WORKOUT_TYPE_KEY]
        if Keys.WORKOUT_SPORT_TYPE_KEY in input:
            self.sport_type = input[Keys.WORKOUT_SPORT_TYPE_KEY]
        if Keys.WORKOUT_WARMUP_KEY in input:
            self.warmup = input[Keys.WORKOUT_WARMUP_KEY]
        if Keys.WORKOUT_COOLDOWN_KEY in input:
            self.cooldown = input[Keys.WORKOUT_COOLDOWN_KEY]
        if Keys.WORKOUT_INTERVALS_KEY in input:
            self.intervals = input[Keys.WORKOUT_INTERVALS_KEY]
        if Keys.WORKOUT_SCHEDULED_TIME_KEY in input and input[Keys.WORKOUT_SCHEDULED_TIME_KEY] is not None:
            self.scheduled_time = datetime.datetime.fromtimestamp(input[Keys.WORKOUT_SCHEDULED_TIME_KEY]).date()
        if Keys.WORKOUT_ESTIMATED_STRESS_KEY in input:
            self.estimated_training_stress = input[Keys.WORKOUT_ESTIMATED_STRESS_KEY]

    def add_warmup(self, seconds):
        """Defines the workout warmup."""
        self.warmup = {}
        self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION] = seconds
        self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERLOW] = 0.25
        self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERHIGH] = 0.75
        self.warmup[ZwoTags.ZWO_ATTR_NAME_PACE] = None

    def add_cooldown(self, seconds):
        """Defines the workout cooldown."""
        self.cooldown = {}
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION] = seconds
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERLOW] = 0.75
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERHIGH] = 0.25
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_PACE] = None

    def add_interval(self, repeat, distance, pace, recovery_distance, recovery_pace):
        """Appends an interval to the workout."""
        interval = {}
        interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY] = int(repeat)
        interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY] = float(distance)
        interval[Keys.INTERVAL_WORKOUT_PACE_KEY] = float(pace)
        interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = float(recovery_distance)
        interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = float(recovery_pace)
        self.intervals.append(interval)

    def export_to_zwo(self, name):
        """Creates a ZWO-formatted file that describes the workout."""
        writer = ZwoWriter.ZwoWriter()
        writer.create_zwo(name)
        writer.store_description(self.type)
        writer.store_sport_type(self.sport_type)
        writer.start_workout()

        # Add the warmup (if applicable).
        if self.warmup is not None:
            writer.store_workout_warmup(self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION], self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.warmup[ZwoTags.ZWO_ATTR_NAME_PACE])

        # Add each interval.
        for interval in self.intervals:

            # Get the details of the interval.
            interval_meters = interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY]
            interval_pace_minute = interval[Keys.INTERVAL_WORKOUT_PACE_KEY]
            recovery_meters = interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY]
            recovery_pace_minute = interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY]

            # Convert distance and pace to time. Distance is given in meters/minute. The final result should be a whole number of seconds.
            on_duration = float(interval_meters) / ((interval_pace_minute) / 60.0)
            on_duration = int(on_duration)
            if recovery_pace_minute == 0:
                recovery_duration = 0
            else:
                recovery_duration = float(recovery_meters) / (float(recovery_pace_minute) / 60.0)
                recovery_duration = int(recovery_duration)
            writer.store_workout_intervals(interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY], on_duration, recovery_duration, None, 0)

        # Add the cooldown (if applicable).
        if self.cooldown is not None:
            writer.store_workout_cooldown(self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.cooldown[ZwoTags.ZWO_ATTR_NAME_PACE])

        writer.end_workout()
        writer.close()

        file_data = writer.buffer()
        return file_data

    def export_to_text(self, unit_system):
        """Creates a string that describes the workout."""

        result  = "Workout Type: "
        result += self.type
        result += "\nSport: "
        result += self.sport_type
        result += "\n"

        # Add the warmup (if applicable).
        if self.warmup is not None and ZwoTags.ZWO_ATTR_NAME_DURATION in self.warmup:
            result += "Warmup: "
            result += str(self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION])
            result += " seconds.\n"

        # Add each interval.
        for interval in self.intervals:

            # Get the details of the interval.
            num_repeats = interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY]
            interval_meters = interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY]
            interval_pace_minute = interval[Keys.INTERVAL_WORKOUT_PACE_KEY]
            recovery_meters = interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY]
            recovery_pace_minute = interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY]

            # Describe the interval.
            result += "Interval: "
            if num_repeats > 1:
                result += str(num_repeats)
                result += " x "
            if interval_meters > 1000:
                result += Units.convert_to_string_in_specified_unit_system(unit_system, interval_meters, Units.UNITS_DISTANCE_METERS, None, Keys.TOTAL_DISTANCE)
            else:
                result += str(int(interval_meters))
                result += " meters"
            if interval_pace_minute > 0:
                result += " at "
                result += Units.convert_to_string_in_specified_unit_system(unit_system, interval_pace_minute, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)

            # Describe the recovery.
            if recovery_meters > 0:
                result += " with "
                if recovery_meters > 1000:
                    result += Units.convert_to_string_in_specified_unit_system(unit_system, recovery_meters, Units.UNITS_DISTANCE_METERS, None, Keys.TOTAL_DISTANCE)
                else:
                    result += str(int(recovery_meters))
                    result += " meters"
                result += " recovery at "
                result += Units.convert_to_string_in_specified_unit_system(unit_system, recovery_pace_minute, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
            result += ".\n"

        # Add the cooldown (if applicable).
        if self.cooldown is not None and ZwoTags.ZWO_ATTR_NAME_DURATION in self.cooldown:
            result += "Cooldown: "
            result += str(self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION])
            result += " seconds.\n"

        # Add an string that describes how this workout fits into the big picture.
        if self.type == Keys.WORKOUT_TYPE_SPEED_RUN:
            result += "Purpose: Speed sessions get you used to running at faster paces.\n"
        elif self.type == Keys.WORKOUT_TYPE_TEMPO_RUN:
            result += "Purpose: Tempo runs build a combination of speed and endurance. They should be performed at a pace you can hold for roughly one hour.\n"
        elif self.type == Keys.WORKOUT_TYPE_EASY_RUN:
            result += "Purpose: Easy runs build aerobic capacity while keeping the wear and tear on the body to a minimum.\n"
        elif self.type == Keys.WORKOUT_TYPE_LONG_RUN:
            result += "Purpose: Long runs build and develop endurance.\n"
        elif self.type == Keys.WORKOUT_TYPE_FREE_RUN:
            result += "Purpose: You should run this at a pace that feels comfortable for you.\n"
        elif self.type == Keys.WORKOUT_TYPE_HILL_REPEATS:
            result += "Purpose: Hill repeats build strength and improve speed.\n"
        elif self.type == Keys.WORKOUT_TYPE_SPEED_INTERVAL_RIDE:
            result += "Purpose: Speed interval sessions get you used to riding at faster paces.\n"
        elif self.type == Keys.WORKOUT_TYPE_TEMPO_RIDE:
            result += "Purpose: Tempo rides build a combination of speed and endurance. They should be performed at an intensity you can hold for roughly one hour.\n"
        elif self.type == Keys.WORKOUT_TYPE_EASY_RIDE:
            result += "Purpose: Easy rides build aerobic capacity while keeping the wear and tear on the body to a minimum.\n"

        if self.estimated_training_stress is not None:
            stress_str = "{:.1f}".format(self.estimated_training_stress)
            result += "Estimated Training Stress: "
            result += stress_str
            result += "\n"

        return result

    def export_to_json_str(self, unit_system):
        """Creates a JSON string that describes the workout."""
        result = self.to_dict()
        result[Keys.WORKOUT_ID_KEY] = str(self.workout_id) # UUIDs aren't serializable, so convert it to a string.
        result[Keys.WORKOUT_DESCRIPTION_KEY] = self.export_to_text(unit_system).replace('\n', '\\n')
        return json.dumps(result, ensure_ascii=False)

    def export_to_ics(self, unit_system):
        """Creates a ICS-formatted data string that describes the workout."""
        ics_writer = IcsWriter.IcsWriter()
        return ics_writer.create_event(self.workout_id, self.scheduled_time, self.scheduled_time, self.type, self.export_to_text(unit_system))

    def calculate_interval_duration(self, interval_meters, interval_pace_meters_per_minute):
        """Utility function for calculating the number of seconds for an interval."""
        interval_duration_secs = interval_meters / (interval_pace_meters_per_minute / 60.0)
        return interval_duration_secs

    def calculate_estimated_training_stress(self, threshold_pace_minute):
        """Computes the estimated training stress for this workout."""
        """May be overridden by child classes, depending on the type of workout."""
        workout_duration_secs = 0.0
        avg_workout_pace = 0.0

        for interval in self.intervals:

            # Get the details of the interval.
            num_repeats = interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY]
            interval_meters = interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY]
            interval_pace_meters_per_minute = interval[Keys.INTERVAL_WORKOUT_PACE_KEY]
            recovery_meters = interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY]
            recovery_pace_meters_per_minute = interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY]

            # Compute the work duration and the average pace.
            if interval_meters > 0 and interval_pace_meters_per_minute > 0.0:
                interval_duration_secs = num_repeats * self.calculate_interval_duration(interval_meters, interval_pace_meters_per_minute)
                workout_duration_secs += interval_duration_secs
                avg_workout_pace += (interval_pace_meters_per_minute * (interval_duration_secs / 60.0))
            if recovery_meters > 0 and recovery_pace_meters_per_minute > 0.0:
                interval_duration_secs = (num_repeats - 1) * self.calculate_interval_duration(recovery_meters, recovery_pace_meters_per_minute)
                workout_duration_secs += interval_duration_secs
                avg_workout_pace += (recovery_pace_meters_per_minute * (interval_duration_secs / 60.0))

        if workout_duration_secs > 0.0:
            avg_workout_pace = avg_workout_pace / workout_duration_secs

        calc = TrainingStressCalculator.TrainingStressCalculator()
        self.estimated_training_stress = calc.estimate_training_stress(workout_duration_secs, avg_workout_pace, threshold_pace_minute)
