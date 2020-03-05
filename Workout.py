# Copyright 2019 Michael J Simms
"""Dscribes a workout to be performed."""

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
        self.user_id = user_id
        self.user_mgr = UserMgr.UserMgr(None)
        self.type = ""
        self.sport_type = ""
        self.scheduled_time = None # The time at which this workout is to be performed
        self.warmup = {} # The warmup interval
        self.cooldown = {} # The cooldown interval
        self.intervals = [] # The workout intervals
        self.needs_rest_day_afterwards = False # Used by the scheduler
        self.can_be_doubled = False # Used by the scheduler to know whether or not this workout can be doubled up with other workouts
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
        else:
            output[Keys.WORKOUT_SCHEDULED_TIME_KEY] = None
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
        interval[Keys.INTERVAL_REPEAT_KEY] = repeat
        interval[Keys.INTERVAL_DISTANCE_KEY] = distance
        interval[Keys.INTERVAL_PACE_KEY] = pace
        interval[Keys.INTERVAL_RECOVERY_DISTANCE_KEY] = recovery_distance
        interval[Keys.INTERVAL_RECOVERY_PACE_KEY] = recovery_pace
        self.intervals.append(interval)

    def export_to_zwo(self, file_name):
        """Creates a ZWO-formatted file that describes the workout."""
        writer = ZwoWriter.ZwoWriter()
        writer.create_zwo(file_name)
        writer.store_description(self.type)
        writer.store_sport_type(self.sport_type)
        writer.start_workout()

        # Add the warmup (if applicable).
        if self.warmup is not None:
            writer.store_workout_warmup(self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION], self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.warmup[ZwoTags.ZWO_ATTR_NAME_PACE])

        # Add each interval.
        for interval in self.intervals:
            interval_meters = interval[Keys.INTERVAL_DISTANCE_KEY]
            interval_pace_minute = interval[Keys.INTERVAL_PACE_KEY]
            recovery_meters = interval[Keys.INTERVAL_RECOVERY_DISTANCE_KEY]
            recovery_pace_minute = interval[Keys.INTERVAL_RECOVERY_PACE_KEY]

            # Convert distance and pace to time. Distance is given in meters/minute. The final result should be a whole number of seconds.
            on_duration = float(interval_meters) / ((interval_pace_minute) / 60.0)
            on_duration = int(on_duration)
            if recovery_pace_minute == 0:
                recovery_duration = 0
            else:
                recovery_duration = float(recovery_meters) / (float(recovery_pace_minute) / 60.0)
                recovery_duration = int(recovery_duration)
            writer.store_workout_intervals(interval[Keys.INTERVAL_REPEAT_KEY], on_duration, recovery_duration, None, 0)

        # Add the cooldown (if applicable).
        if self.cooldown is not None:
            writer.store_workout_cooldown(self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.cooldown[ZwoTags.ZWO_ATTR_NAME_PACE])

        writer.end_workout()
        writer.close()

        file_data = writer.buffer()

        with open(file_name, 'wt') as local_file:
            local_file.write(file_data)

    def export_to_text(self):
        """Creates a string that describes the workout."""
        result  = "Workout Type: "
        result += self.type
        result += "\nSport: "
        result += self.sport_type
        result += "\n"

        # Add the warmup (if applicable).
        if self.warmup is not None and ZwoTags.ZWO_ATTR_NAME_DURATION in self.warmup:
            duration = self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION]

            result += "Warmup: "
            result += str(duration)
            result += " seconds.\n"

        # Add each interval.
        for interval in self.intervals:
            interval_meters = interval[Keys.INTERVAL_DISTANCE_KEY]
            interval_pace_minute = interval[Keys.INTERVAL_PACE_KEY]
            recovery_meters = interval[Keys.INTERVAL_RECOVERY_DISTANCE_KEY]
            recovery_pace_minute = interval[Keys.INTERVAL_RECOVERY_PACE_KEY]

            result += "Interval: "
            result += str(interval_meters)
            result += " meters at "
            result += Units.convert_to_preferred_units_str(self.user_mgr, self.user_id, interval_pace_minute, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_PACE_KEY)
            if recovery_meters > 0:
                result += " with "
                result += str(recovery_meters)
                result += " meters recovery at "
                result += Units.convert_to_preferred_units_str(self.user_mgr, self.user_id, recovery_pace_minute, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, Keys.INTERVAL_PACE_KEY)
            result += ".\n"

        # Add the cooldown (if applicable).
        if self.cooldown is not None and ZwoTags.ZWO_ATTR_NAME_DURATION in self.cooldown:
            duration = self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION]

            result += "Cooldown: "
            result += str(duration)
            result += " seconds.\n"

        # Add an string that describes how this workout fits into the big picture.
        if self.type == Keys.WORKOUT_TYPE_INTERVAL_SESSION:
            result += "Purpose: Interval sessions are designed to build speed and strength.\n"
        elif self.type == Keys.WORKOUT_TYPE_TEMPO_RUN:
            result += "Purpose: Tempo runs build a combination of speed and endurance. They should be performed at a pace you can hold for roughly one hour.\n"
        elif self.type == Keys.WORKOUT_TYPE_EASY_RUN:
            result += "Purpose: Easy runs build aerobic capacity while keeping the wear and tear on the body to a minimum.\n"

        return result

    def export_to_json_str(self):
        """Creates a JSON string that describes the workout."""
        result = self.to_dict()
        result[Keys.WORKOUT_ID_KEY] = str(self.workout_id)
        result[Keys.WORKOUT_DESCRIPTION_KEY] = self.export_to_text()
        return json.dumps(result, ensure_ascii=False)

    def export_to_ics(self, file_name):
        """Creates a ICS-formatted file that describes the workout."""
        ics_writer = IcsWriter.IcsWriter()
        file_data = ics_writer.create(self.workout_id, self.scheduled_time, self.scheduled_time, self.type, self.export_to_text())

        with open(file_name, 'wt') as local_file:
            local_file.write(file_data)
