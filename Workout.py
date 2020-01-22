# Copyright 2019 Michael J Simms

from __future__ import print_function
import json
import inspect
import os
import sys
import IcsWriter
import Keys
import ZwoWriter

# Locate and load the ZwoTags module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
zworeaderdir = os.path.join(currentdir, 'ZwoReader')
sys.path.insert(0, zworeaderdir)
import ZwoTags

class Workout(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.description = ""
        self.sport_type = ""
        self.scheduled_time = None # The time at which this workout is to be performed
        self.warmup = None # The warmup interval
        self.cooldown = None # The cooldown interval
        self.intervals = [] # The workout intervals
        self.needs_rest_day_afterwards = False # Used by the scheduler
        self.can_be_doubled = False # Used by the scheduler to know whether or not this workout can be doubled up with other workouts

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
        writer.store_description(self.description)
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
        result = self.description
        result += "\nSport: "
        result += self.sport_type
        result += "\n"

        # Add the warmup (if applicable).
        if self.warmup is not None:
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
            result += str(interval_pace_minute)
            if recovery_meters > 0:
                result += " with "
                result += str(recovery_meters)
                result += " meters recovery at "
                result += str(recovery_pace_minute)
            result += ".\n"

        # Add the cooldown (if applicable).
        if self.cooldown is not None:
            duration = self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION]

            result += "Cooldown: "
            result += str(duration)
            result += " seconds.\n"

        return result

    def export_to_json(self):
        """Creates a JSON string that describes the workout."""
        result = {}
        result[Keys.WORKOUT_DESCRIPTION_KEY] = self.description
        result[Keys.WORKOUT_SPORT_TYPE_KEY] = self.sport_type
        if self.warmup is not None:
            duration = self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION]
            result[Keys.WORKOUT_WARMUP_KEY] = duration
        if self.intervals is not None:
            result[Keys.WORKOUT_INTERVALS_KEY] = self.intervals
        if self.cooldown is not None:
            duration = self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION]
            result[Keys.WORKOUT_COOLDOWN_KEY] = duration
        return json.dumps(matched_workouts, ensure_ascii=False)

    def export_to_ics(self):
        return ""
