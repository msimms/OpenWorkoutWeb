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

    def gen_easy_run(self, pace, min_distance, max_distance):
        """Utility function for creating an easy run of some random distance between min and max."""
        run_distance = random.uniform(min_distance, max_distance)
        interval_distance = RunPlanGenerator.nearest_interval_distance(run_distance)
        easy_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RUN, self.user_id)
        easy_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        easy_run_workout.add_interval(1, interval_distance, pace, 0, 0)
        return easy_run_workout

    def gen_tempo_run(self, tempo_run_pace):
        """Utility function for creating a tempo workout."""
        interval_distance = RunPlanGenerator.nearest_interval_distance(30.0 * tempo_run_pace)
        tempo_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RUN, self.user_id)
        tempo_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        tempo_run_workout.add_warmup(5 * 60)
        tempo_run_workout.add_interval(1, interval_distance, tempo_run_pace, 0, 0)
        tempo_run_workout.add_cooldown(5 * 60)
        return tempo_run_workout

    def gen_speed_run(self, speed_run_pace, easy_run_pace):
        """Utility function for creating a speed workout."""
        interval_distance = RunPlanGenerator.nearest_interval_distance(10.0 * speed_run_pace)
        speed_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_RUN, self.user_id)
        speed_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        speed_run_workout.add_warmup(10 * 60)
        speed_run_workout.add_interval(1, interval_distance, speed_run_pace, interval_distance * 2, easy_run_pace)
        speed_run_workout.add_cooldown(5 * 60)
        return speed_run_workout

    def gen_interval_run(self, interval_run_pace, easy_run_pace, exp_level):
        """Utility function for creating an interval workout."""

        # Build a collection of possible run interval sessions, sorted by target distance. Order is { reps, distance in meters }.
        interval_workouts = [ [6,100], [6,200], [6,300], [5,600], [4,800], [3,1000], [4,1000], [5,1000], [4,1600], [3,2000], [3,2400] ]
        selected_interval_workout_index = random.randint(0, len(interval_workouts) - 1)
        selected_interval_workout = interval_workouts[selected_interval_workout_index]

        # Alter the number of reps based on the user's skill level.
        if exp_level == Keys.EXPERIENCE_LEVEL_BEGINNER.lower():
            selected_interval_workout[0] = selected_interval_workout[0] - 2
        elif exp_level == Keys.EXPERIENCE_LEVEL_INTERMEDIATE.lower():
            selected_interval_workout[0] = selected_interval_workout[0] - 1

        interval_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_INTERVAL_SESSION, self.user_id)
        interval_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        interval_run_workout.add_warmup(5 * 60)
        interval_run_workout.add_interval(selected_interval_workout[0], selected_interval_workout[1], interval_run_pace, selected_interval_workout[1] * 2, easy_run_pace)
        interval_run_workout.add_cooldown(5 * 60)
        return interval_run_workout

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # 3 Critical runs: Speed session, tempo run, and long run

        goal_distance = inputs[Keys.GOAL_RUN_DISTANCE_KEY]
        goal_type = inputs[Keys.GOAL_TYPE_KEY]
        interval_run_pace = inputs[Keys.INTERVAL_RUN_PACE]
        speed_run_pace = inputs[Keys.SPEED_RUN_PACE]
        tempo_run_pace = inputs[Keys.TEMPO_RUN_PACE]
        long_run_pace = inputs[Keys.LONG_RUN_PACE]
        easy_run_pace = inputs[Keys.EASY_RUN_PACE]
        longest_run_in_four_weeks = inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY]
        avg_run_distance = inputs[Keys.AVG_RUNNING_DISTANCE]
        exp_level = inputs[Keys.EXPERIENCE_LEVEL_KEY]

        # Handle situation in which the user hasn't run in four weeks.
        if longest_run_in_four_weeks is None:
            raise Exception("No runs in the last four weeks.")

        # No pace data?
        if speed_run_pace is None or tempo_run_pace is None or long_run_pace is None or easy_run_pace is None:
            raise Exception("No run pace data.")

        # Long run: 10%/week increase for an experienced runner
        # Taper: 2 weeks for a marathon or more, 1 week for a half marathon or less

        # Compute the longest run needed to accomplish the goal.
        # If the goal distance is a marathon then the longest run should be somewhere between 18 and 22 miles.
        # This equation was derived by playing with trendlines in a spreadsheet.
        max_run_distance = ((-0.002 * goal_distance) *  (-0.002 * goal_distance)) + (0.7 * goal_distance) + 4.4
        max_run_distance = max_run_distance * 1000 # Convert from km to meters

        # Handle situation in which the user is already meeting or exceeding the goal distance.
        if longest_run_in_four_weeks >= max_run_distance:
            longest_run_in_four_weeks = max_run_distance

        # The user cares about speed as well as completing the distance. Also note that we should add strikes to one of the other workouts.
        if goal_type.lower() == Keys.GOAL_TYPE_SPEED.lower():

            # Add an interval session.
            interval_workout = self.gen_interval_run(interval_run_pace, easy_run_pace, exp_level)
            workouts.append(interval_workout)

            # Add a speed session. Start with four intervals, increase the number of intervals as we get closer to the goal.
            speed_workout = self.gen_speed_run(speed_run_pace, easy_run_pace)
            workouts.append(speed_workout)

        # The user only cares about completing the distance so just add another easy run.
        else:

            # Add an easy run.
            easy_run_workout = self.gen_easy_run(easy_run_pace, avg_run_distance * 0.8, avg_run_distance * 1.4)
            workouts.append(easy_run_workout)

        # Add an easy run.
        easy_run_workout = self.gen_easy_run(easy_run_pace, avg_run_distance * 0.8, avg_run_distance * 1.2)
        workouts.append(easy_run_workout)

        # Add a tempo run. Run should be 20-30 minutes in duration.
        tempo_run_workout = self.gen_tempo_run(tempo_run_pace)
        workouts.append(tempo_run_workout)

        # Add a long run.
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
