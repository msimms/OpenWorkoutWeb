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
import IntensityCalculator
import Keys
import Units
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
        self.user_id = user_id                # Unique identifier for the user
        self.activity_type = ""               # Sport (activity) type string
        self.scheduled_time = None            # The time at which this workout is to be performed
        self.warmup = {}                      # The warmup interval
        self.cooldown = {}                    # The cooldown interval
        self.intervals = []                   # The workout intervals
        self.estimated_intensity_score = None # Estimated intensity, the highter, the greater the load on the body
        self.workout_id = uuid.uuid4()        # Unique identifier for the workout

    def __getitem__(self, key):
        if key == Keys.WORKOUT_ID_KEY:
            return self.workout_id
        if key == Keys.WORKOUT_TYPE_KEY:
            return self.type
        if key == Keys.WORKOUT_ACTIVITY_TYPE_KEY:
            return self.activity_type
        if key == Keys.WORKOUT_WARMUP_KEY:
            return self.warmup
        if key == Keys.WORKOUT_COOLDOWN_KEY:
            return self.cooldown
        if key == Keys.WORKOUT_INTERVALS_KEY:
            return self.intervals
        if key == Keys.WORKOUT_SCHEDULED_TIME_KEY and self.scheduled_time is not None:
            dt = time.mktime(self.scheduled_time.timetuple())
            return datetime.datetime(dt.year, dt.month, dt.day)
        if key == Keys.WORKOUT_ESTIMATED_INTENSITY_KEY:
            return self.estimated_intensity_score
        return None

    def to_dict(self):
        """Converts the object representation to a dictionary, only converting what is actually useful, as opposed to __dict__."""
        output = {}
        output[Keys.WORKOUT_ID_KEY] = str(self.workout_id)
        output[Keys.WORKOUT_TYPE_KEY] = self.type
        output[Keys.WORKOUT_ACTIVITY_TYPE_KEY] = self.activity_type
        output[Keys.WORKOUT_WARMUP_KEY] = self.warmup
        output[Keys.WORKOUT_COOLDOWN_KEY] = self.cooldown
        output[Keys.WORKOUT_INTERVALS_KEY] = self.intervals
        if self.scheduled_time is not None:
            output[Keys.WORKOUT_SCHEDULED_TIME_KEY] = time.mktime(self.scheduled_time.timetuple())
        if self.estimated_intensity_score is not None:
            output[Keys.WORKOUT_ESTIMATED_INTENSITY_KEY] = self.estimated_intensity_score
        return output

    def from_dict(self, input):
        """Sets the object's members from a dictionary."""
        if Keys.WORKOUT_ID_KEY in input:
            self.workout_id = input[Keys.WORKOUT_ID_KEY]
        if Keys.WORKOUT_TYPE_KEY in input:
            self.type = input[Keys.WORKOUT_TYPE_KEY]
        if Keys.WORKOUT_ACTIVITY_TYPE_KEY in input:
            self.activity_type = input[Keys.WORKOUT_ACTIVITY_TYPE_KEY]
        if Keys.WORKOUT_WARMUP_KEY in input:
            self.warmup = input[Keys.WORKOUT_WARMUP_KEY]
        if Keys.WORKOUT_COOLDOWN_KEY in input:
            self.cooldown = input[Keys.WORKOUT_COOLDOWN_KEY]
        if Keys.WORKOUT_INTERVALS_KEY in input:
            self.intervals = input[Keys.WORKOUT_INTERVALS_KEY]
        if Keys.WORKOUT_SCHEDULED_TIME_KEY in input and input[Keys.WORKOUT_SCHEDULED_TIME_KEY] is not None:
            self.scheduled_time = datetime.datetime.fromtimestamp(input[Keys.WORKOUT_SCHEDULED_TIME_KEY]).date()
        if Keys.WORKOUT_ESTIMATED_INTENSITY_KEY in input:
            self.estimated_intensity_score = input[Keys.WORKOUT_ESTIMATED_INTENSITY_KEY]

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
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERLOW] = 0.25
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERHIGH] = 0.75
        self.cooldown[ZwoTags.ZWO_ATTR_NAME_PACE] = None

    def add_distance_interval(self, repeat, interval_distance, interval_pace, recovery_distance, recovery_pace):
        """Appends an interval to the workout. The interval is expressed in terms of distance."""
        interval = {}
        interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY] = int(repeat)
        interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY] = float(interval_distance)
        interval[Keys.INTERVAL_WORKOUT_DURATION_KEY] = 0.0
        interval[Keys.INTERVAL_WORKOUT_PACE_KEY] = float(interval_pace)
        interval[Keys.INTERVAL_WORKOUT_POWER_KEY] = 0.0
        if repeat > 1:
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = float(recovery_distance)
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = float(recovery_pace)
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY] = 0.0
        else:
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY] = 0.0
        self.intervals.append(interval)

    def add_time_interval(self, repeat, interval_seconds, interval_pace, recovery_seconds, recovery_pace):
        """Appends an interval to the workout. The interval is expressed in terms of time."""
        interval = {}
        interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY] = int(repeat)
        interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY] = 0.0
        interval[Keys.INTERVAL_WORKOUT_DURATION_KEY] = float(interval_seconds)
        interval[Keys.INTERVAL_WORKOUT_PACE_KEY] = float(interval_pace)
        interval[Keys.INTERVAL_WORKOUT_POWER_KEY] = 0.0
        if repeat > 1:
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY] = float(recovery_seconds)
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = float(recovery_pace)
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY] = 0.0
        else:
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY] = 0.0
        self.intervals.append(interval)

    def add_time_and_power_interval(self, repeat, interval_seconds, interval_power_intensity, recovery_seconds, recovery_power_intensity):
        """Appends an interval to the workout. The interval is expressed in terms of time."""
        interval = {}
        interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY] = int(repeat)
        interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY] = 0.0
        interval[Keys.INTERVAL_WORKOUT_DURATION_KEY] = float(interval_seconds)
        interval[Keys.INTERVAL_WORKOUT_POWER_KEY] = float(interval_power_intensity)
        if repeat > 1:
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY] = float(recovery_seconds)
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY] = float(recovery_power_intensity)
        else:
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY] = 0.0
            interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY] = 0.0
        self.intervals.append(interval)

    def export_to_zwo(self, name):
        """Creates a ZWO-formatted file that describes the workout."""
        writer = ZwoWriter.ZwoWriter()
        writer.create_zwo(name)
        writer.store_description(self.type)
        writer.store_sport_type(self.activity_type)
        writer.start_workout()

        # Add the warmup (if applicable).
        if self.warmup is not None and len(self.warmup) > 0:
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
        if self.cooldown is not None and len(self.cooldown) > 0:
            writer.store_workout_cooldown(self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.cooldown[ZwoTags.ZWO_ATTR_NAME_PACE])

        writer.end_workout()
        writer.close()

        file_data = writer.buffer()
        return file_data

    def export_to_text(self, unit_system):
        """Creates a string that describes the workout."""

        result = self.activity_type
        if len(self.type) > 0:
            result += "\n"
            result += self.type
        result += "\n"

        # Add the warmup (if applicable).
        if self.warmup is not None and ZwoTags.ZWO_ATTR_NAME_DURATION in self.warmup:
            result += "Warmup: "
            result += Units.convert_seconds_to_mins_or_secs(self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION])
            result += ".\n"

        # Add each interval.
        if len(self.intervals) == 0:
            result += "Steady state, no specified intensity"
        for interval in self.intervals:

            num_repeats = 0
            interval_distance = 0
            interval_duration = 0
            interval_pace = 0
            interval_power = 0
            recovery_distance = 0
            recovery_duration = 0
            recovery_pace = 0
            recovery_power = 0

            # Get the details of the interval.
            if Keys.INTERVAL_WORKOUT_REPEAT_KEY in interval:
                num_repeats = interval[Keys.INTERVAL_WORKOUT_REPEAT_KEY]
            if Keys.INTERVAL_WORKOUT_DISTANCE_KEY in interval:
                interval_distance = interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY]
            if Keys.INTERVAL_WORKOUT_DURATION_KEY in interval:
                interval_duration = interval[Keys.INTERVAL_WORKOUT_DURATION_KEY]
            if Keys.INTERVAL_WORKOUT_PACE_KEY in interval:
                interval_pace = interval[Keys.INTERVAL_WORKOUT_PACE_KEY]
            if Keys.INTERVAL_WORKOUT_POWER_KEY in interval:
                interval_power = interval[Keys.INTERVAL_WORKOUT_POWER_KEY]
            if Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY in interval:
                recovery_distance = interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY]
            if Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY in interval:
                recovery_duration = interval[Keys.INTERVAL_WORKOUT_RECOVERY_DURATION_KEY]
            if Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY in interval:
                recovery_pace = interval[Keys.INTERVAL_WORKOUT_RECOVERY_PACE_KEY]
            if Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY in interval:
                recovery_power = interval[Keys.INTERVAL_WORKOUT_RECOVERY_POWER_KEY]

            #
            # Describe the interval.
            #

            result += "Interval: "

            # Only print the multiplier if there's more than one interval.
            if num_repeats > 1:
                result += str(num_repeats)
                result += " x "

            # Add the interval distance.
            if interval_distance > 0:
                result += Units.convert_meters_to_printable(unit_system, interval_distance)

            # Add the interval duration.
            elif interval_duration > 0:
                result += Units.convert_seconds_to_mins_or_secs(int(interval_duration))
                result += " "

            # Add the interval pace.
            if interval_pace > 0:
                result += " at "
                if unit_system:
                    result += Units.convert_to_string_in_specified_unit_system(unit_system, interval_pace, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
                else:
                    result += Units.convert_to_string_in_specified_unit_system(Keys.UNITS_METRIC_KEY, interval_pace, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
                    result += " ("
                    result += Units.convert_to_string_in_specified_unit_system(Keys.UNITS_STANDARD_KEY, interval_pace, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
                    result += ")"

            # Add the interval power.
            if interval_power > 0:
                result += " at "
                result += str(int(interval_power))
                result += "% FTP"

            # Add the recovery distance.
            if recovery_distance > 0:
                result += " with "
                result += Units.convert_meters_to_printable(unit_system, recovery_distance)
                result += " recovery at "
                if unit_system:
                    result += Units.convert_to_string_in_specified_unit_system(unit_system, recovery_pace, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
                else:
                    result += Units.convert_to_string_in_specified_unit_system(Keys.UNITS_METRIC_KEY, recovery_pace, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
                    result += " ("
                    result += Units.convert_to_string_in_specified_unit_system(Keys.UNITS_STANDARD_KEY, recovery_pace, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_WORKOUT_PACE_KEY)
                    result += ")"

            # Add the recovery duration.
            elif recovery_duration > 0:
                result += " with "
                result += Units.convert_seconds_to_mins_or_secs(int(recovery_duration))
                result += " recovery "

            # Add the recovery power.
            if recovery_power > 0:
                result += " at "
                result += str(int(recovery_power * 100.0))
                result += "% FTP"

            result += ".\n"

        # Add the cooldown (if applicable).
        if self.cooldown is not None and ZwoTags.ZWO_ATTR_NAME_DURATION in self.cooldown:
            result += "Cooldown: "
            result += Units.convert_seconds_to_mins_or_secs(self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION])
            result += ".\n"

        # Add an string that describes how this workout fits into the big picture.
        if self.type == Keys.WORKOUT_TYPE_EVENT:
            result += "Goal Event!\n"
        elif self.type == Keys.WORKOUT_TYPE_SPEED_RUN:
            result += "Purpose: Speed sessions get you used to running at faster paces.\n"
        elif self.type == Keys.WORKOUT_TYPE_THRESHOLD_RUN:
            result += "Purpose: Tempo runs build a combination of speed and endurance. They should be performed at a pace you can hold for roughly one hour.\n"
        elif self.type == Keys.WORKOUT_TYPE_TEMPO_RUN:
            result += "Purpose: Tempo runs build a combination of speed and endurance. They should be performed at a pace slightly slower than your pace for a 5K race.\n"
        elif self.type == Keys.WORKOUT_TYPE_EASY_RUN:
            result += "Purpose: Easy runs build aerobic capacity while keeping the wear and tear on the body to a minimum. Pacing should be slow enough to stay at or near Heart Rate Zone 2, i.e. conversational pace.\n"
        elif self.type == Keys.WORKOUT_TYPE_LONG_RUN:
            result += "Purpose: Long runs build and develop endurance.\n"
        elif self.type == Keys.WORKOUT_TYPE_FREE_RUN:
            result += "Purpose: You should run this at a pace that feels comfortable for you.\n"
        elif self.type == Keys.WORKOUT_TYPE_HILL_REPEATS:
            result += "Purpose: Hill repeats build strength and improve speed.\n"
        elif self.type == Keys.WORKOUT_TYPE_PROGRESSION_RUN:
            result += "Purpose: Progression runs teach you to run fast on tired legs.\n"
        elif self.type == Keys.WORKOUT_TYPE_FARTLEK_RUN:
            result += "Purpose: Fartlek sessions combine speed and endurance without the formal structure of a traditional interval workout.\n"
        elif self.type == Keys.WORKOUT_TYPE_MIDDLE_DISTANCE_RUN:
            result += "Purpose: Middle distance runs help build stamina."
        elif self.type == Keys.WORKOUT_TYPE_HILL_RIDE:
            result += "Purpose: Hill workouts build the strength needed to tackle hills in a race. This can be done on the indoor trainer or replaced with low gear work if hills are not available.\n"
        elif self.type == Keys.WORKOUT_TYPE_SPEED_INTERVAL_RIDE:
            result += "Purpose: Speed interval sessions get you used to riding at faster paces.\n"
        elif self.type == Keys.WORKOUT_TYPE_TEMPO_RIDE:
            result += "Purpose: Tempo rides build a combination of speed and endurance. They should be performed at a pace you can hold for roughly one hour.\n"
        elif self.type == Keys.WORKOUT_TYPE_EASY_RIDE:
            result += "Purpose: Easy rides build aerobic capacity while keeping the wear and tear on the body to a minimum.\n"
        elif self.type == Keys.WORKOUT_TYPE_SWEET_SPOT_RIDE:
            result += "Purpose: Sweet spot rides are hard enough to improve fitness while being easy enough to do frequently.\n"
        elif self.type == Keys.WORKOUT_TYPE_OPEN_WATER_SWIM:
            result += "Purpose: Open water swims get you used to race day conditions.\n"
        elif self.type == Keys.WORKOUT_TYPE_POOL_SWIM:
            result += "Purpose: Most training is done in the swimming pool.\n"
        elif self.type == Keys.WORKOUT_TYPE_TECHNIQUE_SWIM:
            result += "Purpose: Develop proper swimming technique.\n"

        # Add the intensity score, if it's been computed.
        if self.estimated_intensity_score is not None:
            stress_str = "{:.1f}".format(self.estimated_intensity_score)
            result += "Estimated Intensity Score: "
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

    def total_workout_distance_meters(self):
        """Returns the total workout distance, in meters."""
        total_meters = 0.0
        for interval in self.intervals:
            total_meters = total_meters + interval[Keys.INTERVAL_WORKOUT_DISTANCE_KEY]
            total_meters = total_meters + interval[Keys.INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY]
        return total_meters

    def calculate_interval_duration(self, interval_meters, interval_pace_meters_per_minute):
        """Utility function for calculating the number of seconds for an interval."""
        interval_duration_secs = interval_meters / (interval_pace_meters_per_minute / 60.0)
        return interval_duration_secs

    def calculate_estimated_intensity_score(self, threshold_pace_meters_per_minute):
        """Computes the estimated intensity for this workout."""
        """May be overridden by child classes, depending on the type of workout."""
        workout_duration_secs = 0.0
        avg_workout_pace_meters_per_sec = 0.0

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
                avg_workout_pace_meters_per_sec += (interval_pace_meters_per_minute * (interval_duration_secs / 60.0))
            if recovery_meters > 0 and recovery_pace_meters_per_minute > 0.0:
                interval_duration_secs = num_repeats * self.calculate_interval_duration(recovery_meters, recovery_pace_meters_per_minute)
                workout_duration_secs += interval_duration_secs
                avg_workout_pace_meters_per_sec += (recovery_pace_meters_per_minute * (interval_duration_secs / 60.0))

        if workout_duration_secs > 0.0:
            avg_workout_pace_meters_per_sec = avg_workout_pace_meters_per_sec / workout_duration_secs

        calc = IntensityCalculator.IntensityCalculator()
        self.estimated_intensity_score = calc.estimate_intensity_score(workout_duration_secs, avg_workout_pace_meters_per_sec, threshold_pace_meters_per_minute * 60.0)
