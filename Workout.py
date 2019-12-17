# Copyright 2019 Michael J Simms

from __future__ import print_function
import ZwoWriter

class Workout(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.description = ""
        self.sport_type = ""
        self.intervals = []

    def export_to_zwo(self, file_name):
        writer = ZwoWriter.ZwoWriter()
        writer.create_zwo(file_name)
        writer.store_description(self.description)
        writer.store_sport_type(self.sport_type)
        writer.start_workout()
        for interval in self.intervals:
            pass
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
