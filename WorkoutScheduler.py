# Copyright 2019 Michael J Simms

import IcsWriter

class WorkoutScheduler(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def schedule_workouts(self, workouts):
        """Organizes the workouts into a schedule for the next week."""
        return workouts

    def export_to_ics(self, workouts):
        """Exports the workouts to ICS files."""
        for workout in workouts:
            pass
