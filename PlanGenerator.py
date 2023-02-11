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

    def is_goal_week(self, goal, weeks_until_goal, goal_distance):
        return goal != Keys.GOAL_FITNESS_KEY and weeks_until_goal < 1.0 and PlanGenerator.PlanGenerator.valid_float(goal_distance)

    def is_in_taper(self, weeks_until_goal, goal):
        """Taper: 2 weeks for a marathon or more, 1 week for a half marathon or less."""
        in_taper = False
        if weeks_until_goal is not None:
            if weeks_until_goal <= 2 and (goal == Keys.GOAL_50K_RUN_KEY or goal == Keys.GOAL_50_MILE_RUN_KEY):
                in_taper = True
            if weeks_until_goal <= 2 and (goal == Keys.GOAL_MARATHON_RUN_KEY or goal == Keys.GOAL_IRON_DISTANCE_TRIATHLON_KEY):
                in_taper = True
            if weeks_until_goal <= 1 and (goal == Keys.GOAL_HALF_MARATHON_RUN_KEY or goal == Keys.GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY):
                in_taper = True
        return in_taper

    def is_time_for_an_easy_week(self, total_intensity_week_1, total_intensity_week_2, total_intensity_week_3, total_intensity_week_4):
        """Is it time for an easy week? After four weeks of building we should include an easy week to mark the end of a block."""
        easy_week = False
        if total_intensity_week_1 and total_intensity_week_2 and total_intensity_week_3 and total_intensity_week_4:
            if total_intensity_week_1 >= total_intensity_week_2 and total_intensity_week_2 >= total_intensity_week_3 and total_intensity_week_3 >= total_intensity_week_4:
                easy_week = True
        return easy_week

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""
        return []
