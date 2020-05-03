# Copyright 2019 Michael J Simms
"""Generates a run plan for the specifiied user."""

import math
import numpy as np
import random

import Keys
import TrainingPaceCalculator
import Workout
import WorkoutFactory

class RunPlanGenerator(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    @staticmethod
    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    @staticmethod
    def nearest_interval_distance(distance):
        """Given a distance, returns the nearest 'common' interval distance,"""
        """i.e., if given 407 meters, returns 400 meters, because no one runs 407 meter intervals."""
        metric_intervals = [400, 800, 1000, 2000, 5000]
        us_customary_intervals = [0.25, 0.5, 1]
        return RunPlanGenerator.find_nearest(metric_intervals, distance)

    @staticmethod
    def round_distance(distance):
        return float(math.ceil(distance / 100.0)) * 100.0

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        # 3 Critical runs: Speed session, tempo run, and long run
        # Long run: 10%/week increase for an experienced runner
        # Taper: 2 weeks for a marathon or more, 1 week for a half marathon or less

        goal_distance = inputs[Keys.GOAL_RUN_DISTANCE_KEY]
        goal_type = inputs[Keys.GOAL_TYPE_KEY]
        interval_run_pace = inputs[Keys.INTERVAL_RUN_PACE]
        speed_run_pace = inputs[Keys.SPEED_RUN_PACE]
        tempo_run_pace = inputs[Keys.TEMPO_RUN_PACE]
        long_run_pace = inputs[Keys.LONG_RUN_PACE]
        easy_run_pace = inputs[Keys.EASY_RUN_PACE]
        longest_run_in_four_weeks = inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY]

        # Compute the longest run needed to accomplish the goal.
        # This equation was derived by playing with trendlines in Apple Numbers.
        # If the goal distance is a marathon then the longest run should be somewhere between 18 and 22 miles.
        max_run_distance = ((-0.002 * goal_distance) *  (-0.002 * goal_distance)) + (0.7 * goal_distance) + 4.4
        max_run_distance = max_run_distance * 1000 # Convert from km to meters

        # Handle situation in which the user hasn't run in four weeks
        if longest_run_in_four_weeks is None:
            raise Exception("No runs in the last four weeks.")

        # No pace data?
        if speed_run_pace is None or tempo_run_pace is None or long_run_pace is None or easy_run_pace is None:
            raise Exception("No run pace data.")

        # Handle situation in which the user is already meeting or exceeding the goal distance.
        if longest_run_in_four_weeks >= max_run_distance:
            longest_run_in_four_weeks = max_run_distance

        workouts = []

        # The user cares about speed as well as completing the distance. Also note that we should add strikes to one of the other workouts.
        if goal_type.lower() == Keys.GOAL_TYPE_SPEED.lower():

            # Build a collection of possible run interval sessions, sorted by target distance. Order is { reps, distance in meters }.
            interval_workouts = [ [6,100], [6,200], [6,300], [5,600], [4,800], [3,1000], [4,1000], [5,1000], [4,1600], [3,2000], [3,2400] ]

            # Add an interval session.
            selected_interval_workout_index = random.randint(0, len(interval_workouts) - 1)
            selected_interval_workout = interval_workouts[selected_interval_workout_index]
            interval_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_INTERVAL_SESSION, self.user_id)
            interval_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
            interval_run_workout.add_warmup(5 * 60)
            interval_run_workout.add_interval(selected_interval_workout[0], selected_interval_workout[1], interval_run_pace, selected_interval_workout[1] * 2, easy_run_pace)
            interval_run_workout.add_cooldown(5 * 60)
            workouts.append(interval_run_workout)

            # Add another speed session. Start with four intervals, increase the number of intervals as we get closer to the goal.
            interval_distance = RunPlanGenerator.nearest_interval_distance(10.0 * speed_run_pace)
            speed_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_RUN, self.user_id)
            speed_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
            speed_run_workout.add_warmup(10 * 60)
            speed_run_workout.add_interval(1, interval_distance, speed_run_pace, interval_distance * 2, easy_run_pace)
            speed_run_workout.add_cooldown(5 * 60)
            workouts.append(speed_run_workout)

        # The user only cares about completing the distance.
        else:

            # Add an easy run.
            interval_distance = RunPlanGenerator.nearest_interval_distance(longest_run_in_four_weeks / 5)
            easy_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RUN, self.user_id)
            easy_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
            easy_run_workout.add_interval(1, interval_distance, easy_run_pace, 0, 0)
            workouts.append(easy_run_workout)

        # Add a tempo run. Run should be 20-30 minutes in duration.
        interval_distance = RunPlanGenerator.nearest_interval_distance(30.0 * tempo_run_pace)
        tempo_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RUN, self.user_id)
        tempo_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        tempo_run_workout.add_warmup(5 * 60)
        tempo_run_workout.add_interval(1, interval_distance, tempo_run_pace, 0, 0)
        tempo_run_workout.add_cooldown(5 * 60)
        workouts.append(tempo_run_workout)

        # Add a long run
        long_run_distance = longest_run_in_four_weeks * 1.1
        if long_run_distance > max_run_distance:
            long_run_distance = max_run_distance 
        interval_distance = RunPlanGenerator.round_distance(long_run_distance)
        long_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_LONG_RUN, self.user_id)
        long_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        long_run_workout.add_interval(1, interval_distance, long_run_pace, 0, 0)
        long_run_workout.needs_rest_day_afterwards = True
        workouts.append(long_run_workout)

        return workouts
