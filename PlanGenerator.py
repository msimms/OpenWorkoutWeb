# Copyright 2022 Michael J Simms
"""Base class for all plan generators."""

import Keys

class PlanGenerator(object):
    """Base class for all plan generators."""

    def __init__(self, user_id):
        self.user_id = user_id

    @staticmethod
    def valid_float(value):
        return type(value) == float and value > 0.1

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    def is_in_taper(self, weeks_until_goal, goal):
        """Taper: 2 weeks for a marathon or more, 1 week for a half marathon or less."""
        in_taper = False
        if weeks_until_goal is not None:
            if weeks_until_goal <= 2 and (goal == Keys.GOAL_MARATHON_RUN_KEY or goal == Keys.GOAL_IRON_DISTANCE_TRIATHLON_KEY):
                in_taper = True
            if weeks_until_goal <= 1 and (goal == Keys.GOAL_HALF_MARATHON_RUN_KEY or goal == Keys.GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY):
                in_taper = True
        return in_taper

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""
        return []
