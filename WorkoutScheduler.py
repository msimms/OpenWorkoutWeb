# Copyright 2019 Michael J Simms

class WorkoutScheduler(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def schedule_workouts(self, workouts):
        """Organizes the workouts into a schedule for the next week."""
        return workouts
