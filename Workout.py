# Copyright 2019 Michael J Simms

from __future__ import print_function
import inspect
import os
import sys
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
        self.warmup = None
        self.cooldown = None
        self.intervals = []

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
        if self.warmup is not None:
            writer.store_workout_warmup(self.warmup[ZwoTags.ZWO_ATTR_NAME_DURATION], self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.warmup[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.warmup[ZwoTags.ZWO_ATTR_NAME_PACE])
        for interval in self.intervals:
            on_duration = float(interval[Keys.INTERVAL_DISTANCE_KEY]) * float(interval[Keys.INTERVAL_PACE_KEY])
            recovery_duration = float(interval[Keys.INTERVAL_RECOVERY_DISTANCE_KEY]) * float(interval[Keys.INTERVAL_RECOVERY_PACE_KEY])
            writer.store_workout_intervals(interval[Keys.INTERVAL_REPEAT_KEY], on_duration, recovery_duration, None, None)
        if self.cooldown is not None:
            writer.store_workout_cooldown(self.cooldown[ZwoTags.ZWO_ATTR_NAME_DURATION], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERLOW], self.cooldown[ZwoTags.ZWO_ATTR_NAME_POWERHIGH], self.cooldown[ZwoTags.ZWO_ATTR_NAME_PACE])
        writer.end_workout()
        writer.close()

        file_data = writer.buffer()

        with open(file_name, 'wt') as local_file:
            local_file.write(file_data)

    def print(*args, **kwargs):
        """For debugging purposes. Prints details to standard output."""
        __builtin__.print(self.description)
        __builtin__.print(self.distance_in_meters)
        return __builtin__.print(*args, **kwargs)
