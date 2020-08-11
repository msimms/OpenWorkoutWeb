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
        self.easy_distance_total_meters = 0.0
        self.hard_distance_total_meters = 0.0

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    @staticmethod
    def valid_float(value):
        return type(value) == float and value > 0.1

    @staticmethod
    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    @staticmethod
    def nearest_interval_distance(distance, min_distance_in_meters):
        """Given a distance, returns the nearest 'common' interval distance,"""
        """i.e., if given 407 meters, returns 400 meters, because no one runs 407 meter intervals."""
        if distance < min_distance_in_meters:
            distance = min_distance_in_meters
        metric_intervals = [ 400, 800, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 12000, 15000, 20000, 21000 ]
        us_customary_intervals = [ 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 3.1, 5.0, 6.0, 6.2, 8.0, 10.0, 12.0, 13.1 ]
        return RunPlanGenerator.find_nearest(metric_intervals, distance)

    @staticmethod
    def round_distance(distance):
        return float(math.ceil(distance / 100.0)) * 100.0

    def gen_easy_run(self, pace, min_run_distance, max_run_distance):
        """Utility function for creating an easy run of some random distance between min and max."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(min_run_distance, max_run_distance)
        if run_distance > 1000:
            interval_distance_meters = round(run_distance, -3)
        else:
            interval_distance_meters = round(run_distance, -2)

        # Create the workout object.
        easy_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RUN, self.user_id)
        easy_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        easy_run_workout.add_interval(1, interval_distance_meters, pace, 0, 0)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += interval_distance_meters

        return easy_run_workout

    def gen_tempo_run(self, tempo_run_pace, easy_run_pace, max_run_distance):
        """Utility function for creating a tempo workout."""

        temp_distance = 30.0 * tempo_run_pace
        interval_distance_meters = RunPlanGenerator.nearest_interval_distance(temp_distance, 2000.0)

        # Sanity check.
        if interval_distance_meters > max_run_distance:
            interval_distance_meters = max_run_distance

        warmup_duration = 10 * 60
        cooldown_duration = 10 * 60

        # Create the workout object.
        tempo_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RUN, self.user_id)
        tempo_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        tempo_run_workout.add_warmup(warmup_duration)
        tempo_run_workout.add_interval(1, interval_distance_meters, tempo_run_pace, 0, 0)
        tempo_run_workout.add_cooldown(cooldown_duration)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += (warmup_duration / easy_run_pace)
        self.easy_distance_total_meters += (cooldown_duration / easy_run_pace)
        self.hard_distance_total_meters += interval_distance_meters

        return tempo_run_workout

    def gen_speed_run(self, short_interval_run_pace, speed_run_pace, easy_run_pace):
        """Utility function for creating a speed/interval workout."""

        # Constants.
        MIN_REPS_INDEX = 0
        MAX_REPS_INDEX = 1
        REP_DISTANCE_INDEX = 2

        warmup_duration = 10 * 60
        cooldown_duration = 10 * 60

        # Build a collection of possible run interval sessions, sorted by target distance. Order is { min reps, max reps, distance in meters }.
        possible_workouts = [ [ 4, 6, 100 ], [ 4, 6, 200 ], [ 4, 6, 400 ], [ 4, 6, 600 ], [ 2, 4, 800 ], [ 2, 4, 1000 ], [ 2, 4, 1600 ] ]
        selected_interval_workout = random.choice(possible_workouts)

        # Determine the pace for this workout.
        if selected_interval_workout[REP_DISTANCE_INDEX] < 1000:
            interval_pace = short_interval_run_pace
        else:
            interval_pace = speed_run_pace

        # Determine the number of reps for this workout.
        selected_reps = random.randint(selected_interval_workout[MIN_REPS_INDEX], selected_interval_workout[MAX_REPS_INDEX])

        # Determine the distance for this workout.
        interval_distance = selected_interval_workout[REP_DISTANCE_INDEX]
        rest_interval_distance = interval_distance * 2

        # Create the workout object.
        interval_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_RUN, self.user_id)
        interval_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        interval_run_workout.add_warmup(warmup_duration)
        interval_run_workout.add_interval(selected_reps, interval_distance, interval_pace, rest_interval_distance, easy_run_pace)
        interval_run_workout.add_cooldown(cooldown_duration)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += (warmup_duration / easy_run_pace)
        self.easy_distance_total_meters += (cooldown_duration / easy_run_pace)
        self.easy_distance_total_meters += ((selected_reps - 1) * rest_interval_distance)
        self.hard_distance_total_meters += (selected_reps * interval_distance)

        return interval_run_workout

    def gen_long_run(self, long_run_pace, longest_run_in_four_weeks, min_run_distance, max_run_distance):
        """Utility function for creating a long run workout."""

        # Long run should be 10% longer than the previous long run, within the bounds provided by min and max.
        long_run_distance = longest_run_in_four_weeks * 1.1
        if long_run_distance > max_run_distance:
            long_run_distance = max_run_distance
        if long_run_distance < min_run_distance:
            long_run_distance = min_run_distance
        interval_distance_meters = RunPlanGenerator.round_distance(long_run_distance)

        # Create the workout object.
        long_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_LONG_RUN, self.user_id)
        long_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        long_run_workout.add_interval(1, interval_distance_meters, long_run_pace, 0, 0)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += interval_distance_meters

        return long_run_workout

    def gen_free_run(self):
        """Utility function for creating a free run workout."""

        # Create the workout object.
        long_run_workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_FREE_RUN, self.user_id)
        long_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        long_run_workout.add_interval(1, 5000, 0, 0, 0)

        return long_run_workout

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # 3 Critical runs: Speed session, tempo run, and long run

        goal_distance = inputs[Keys.GOAL_RUN_DISTANCE_KEY]
        goal_type = inputs[Keys.GOAL_TYPE_KEY]
        short_interval_run_pace = inputs[Keys.SHORT_INTERVAL_RUN_PACE]
        functional_threshold_pace = inputs[Keys.FUNCTIONAL_THRESHOLD_PACE]
        speed_run_pace = inputs[Keys.SPEED_RUN_PACE]
        tempo_run_pace = inputs[Keys.TEMPO_RUN_PACE]
        long_run_pace = inputs[Keys.LONG_RUN_PACE]
        easy_run_pace = inputs[Keys.EASY_RUN_PACE]
        longest_run_in_four_weeks = inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY]
        longest_run_week_1 = inputs[Keys.LONGEST_RUN_WEEK_1_KEY]
        longest_run_week_2 = inputs[Keys.LONGEST_RUN_WEEK_2_KEY]
        longest_run_week_3 = inputs[Keys.LONGEST_RUN_WEEK_3_KEY]
        in_taper = inputs[Keys.IN_TAPER_KEY]
        avg_run_distance = inputs[Keys.AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS]
        exp_level = inputs[Keys.EXPERIENCE_LEVEL_KEY]

        # Handle situation in which the user hasn't run in four weeks.
        if not RunPlanGenerator.valid_float(longest_run_in_four_weeks):
            workouts.append(self.gen_free_run())
            workouts.append(self.gen_free_run())
            return workouts

        # No pace data?
        if not (RunPlanGenerator.valid_float(short_interval_run_pace) and RunPlanGenerator.valid_float(speed_run_pace) and RunPlanGenerator.valid_float(tempo_run_pace) and RunPlanGenerator.valid_float(long_run_pace) and RunPlanGenerator.valid_float(easy_run_pace)):
            raise Exception("No run pace data.")

        # If the long run has been increasing for the last three weeks then give the person a break.
        if longest_run_week_1 and longest_run_week_2 and longest_run_week_3:
            if longest_run_week_1 >= longest_run_week_2 and longest_run_week_2 >= longest_run_week_3:
                longest_run_in_four_weeks *= 0.75

        # Compute the longest run needed to accomplish the goal.
        # If the goal distance is a marathon then the longest run should be somewhere between 18 and 22 miles.
        # This equation was derived by playing with trendlines in a spreadsheet.
        max_long_run_distance = ((-0.002 * goal_distance) *  (-0.002 * goal_distance)) + (0.7 * goal_distance) + 4.4

        # Handle situation in which the user is already meeting or exceeding the goal distance.
        if longest_run_in_four_weeks >= max_long_run_distance:
            longest_run_in_four_weeks = max_long_run_distance

        # Distance ceilings for easy and tempo runs.
        max_easy_run_distance = longest_run_in_four_weeks * 0.75
        max_tempo_run_distance = longest_run_in_four_weeks * 0.50

        # Don't make any runs (other than intervals, tempo runs, etc.) shorter than this.
        min_run_distance = avg_run_distance * 0.5
        if min_run_distance > max_easy_run_distance:
            min_run_distance = max_easy_run_distance

        # We'll also set the percentage of easy miles/kms based on the experience level.
        if exp_level == Keys.EXPERIENCE_LEVEL_BEGINNER.lower():
            min_easy_distance_percentage = 0.9
        else:
            min_easy_distance_percentage = 0.8

        iter_count = 0
        done = False
        while not done:

            workouts = []

            # Keep track of the number of easy miles/kms and the number of hard miles/kms we're expecting the user to run so we can balance the two.
            self.easy_distance_total_meters = 0.0
            self.hard_distance_total_meters = 0.0

            # The user cares about speed as well as completing the distance. Also note that we should add strikes to one of the other workouts.
            if goal_type.lower() == Keys.GOAL_TYPE_SPEED.lower():

                # Add an interval/speed session.
                interval_workout = self.gen_speed_run(short_interval_run_pace, speed_run_pace, easy_run_pace)
                workouts.append(interval_workout)

                # (Maybe) add another interval/speed session, unless it's pushing us over our allowed amount of hard distance for the week.
                if iter_count <= 1:
                    interval_workout = self.gen_speed_run(short_interval_run_pace, speed_run_pace, easy_run_pace)
                    workouts.append(interval_workout)
                else:
                    easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
                    workouts.append(easy_run_workout)

            # The user only cares about completing the distance so just add another easy run.
            else:

                # Add an easy run.
                easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
                workouts.append(easy_run_workout)

            # Add an easy run.
            easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
            workouts.append(easy_run_workout)

            # Add a tempo run. Run should be 20-30 minutes in duration.
            tempo_run_workout = self.gen_tempo_run(tempo_run_pace, easy_run_pace, max_tempo_run_distance)
            workouts.append(tempo_run_workout)

            # Add a long run.
            long_run_workout = self.gen_long_run(long_run_pace, longest_run_in_four_weeks, min_run_distance, max_long_run_distance)
            workouts.append(long_run_workout)

            # Keep track of the total distance as well as the easy distance to keep from planning too many intense miles/kms.
            total_distance = self.easy_distance_total_meters + self.hard_distance_total_meters
            easy_distance_percentage = self.easy_distance_total_meters / total_distance

            # This is used to make sure we don't loop forever.
            iter_count = iter_count + 1

            # Exit conditions:
            if iter_count >= 6:
                done = True
            if easy_distance_percentage >= min_easy_distance_percentage:
                done = True

        # Calculate the total stress for each workout.
        for workout in workouts:
            workout.calculate_estimated_training_stress(functional_threshold_pace)

        return workouts
