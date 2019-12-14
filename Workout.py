# Copyright 2019 Michael J Simms

from __future__ import print_function

class Workout(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.description = ""
        self.intervals = []

    def export_to_zwo(self):
        pass

    def print(*args, **kwargs):
        """For debugging purposes. Prints details to standard output."""
        __builtin__.print(self.description)
        __builtin__.print(self.distance_in_meters)
        return __builtin__.print(*args, **kwargs)
