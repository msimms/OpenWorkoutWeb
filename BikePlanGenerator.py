# Copyright 2019 Michael J Simms
"""Generates a bike plan for the specifiied user."""

class BikePlanGenerator(object):
    """Class for generating a bike plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # Add critical workouts:
        # Long ride, culminating in (maybe) an overdistance ride.

        return workouts
