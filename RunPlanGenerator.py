# Copyright 2019 Michael J Simms
"""Generates a run plan for the specifiied user."""

import math
import numpy as np
import random
from scipy.stats import norm

import Keys
import TrainingPaceCalculator
import Units
import Workout
import WorkoutFactory

METERS_PER_HALF_MARATHON = 13.1 * Units.METERS_PER_MILE
METERS_PER_MARATHON = 26.2 * Units.METERS_PER_MILE

class RunPlanGenerator(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.easy_distance_total_meters = 0.0
        self.hard_distance_total_meters = 0.0
        self.total_easy_seconds = 0.0 # Total weekly minutes spent running easy
        self.total_hard_seconds = 0.0 # Total weekly minutes spent running hard

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
        metric_intervals = [ 400, 800, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 12000, 15000, 20000, 21000, 25000 ]
        us_customary_intervals = [ 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 3.1, 5.0, 6.0, 6.2, 8.0, 10.0, 12.0, 13.1 ]
        return RunPlanGenerator.find_nearest(metric_intervals, distance)

    @staticmethod
    def round_distance(distance):
        return float(math.ceil(distance / 100.0)) * 100.0

    def gen_easy_run(self, pace, min_run_distance, max_run_distance):
        """Utility function for creating an easy run of some random distance between min and max."""

        # An easy run needs to be at least a couple of kilometers.
        if min_run_distance < 2000:
            min_run_distance = 2000
        if max_run_distance < 2000:
            max_run_distance = 2000

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(min_run_distance, max_run_distance)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RUN, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_interval(1, interval_distance_meters, pace, 0, 0)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += interval_distance_meters

        # Tally up the easy and hard seconds.
        self.total_easy_seconds += interval_distance_meters * pace

        return workout

    def gen_tempo_run(self, tempo_run_pace, easy_run_pace, max_run_distance):
        """Utility function for creating a tempo workout."""

	    # Decide on the number of intervals and their distance.
        num_intervals = 1
        temp_distance = (30.0 * tempo_run_pace) / num_intervals
        interval_distance_meters = RunPlanGenerator.nearest_interval_distance(temp_distance, 2000.0)

        # Sanity check.
        if interval_distance_meters > max_run_distance:
            interval_distance_meters = max_run_distance
        if interval_distance_meters < 1000:
            interval_distance_meters = 1000

        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RUN, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_interval(num_intervals, interval_distance_meters, tempo_run_pace, 0, 0)
        workout.add_cooldown(cooldown_duration)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        total_rest_meters = ((num_intervals - 1) * interval_distance_meters)
        total_hard_meters = (num_intervals * interval_distance_meters)
        self.easy_distance_total_meters += (warmup_duration / easy_run_pace)
        self.easy_distance_total_meters += (cooldown_duration / easy_run_pace)
        self.easy_distance_total_meters += (total_rest_meters)
        self.hard_distance_total_meters += (total_hard_meters)

        # Tally up the easy and hard seconds.
        self.total_easy_seconds += (warmup_duration + cooldown_duration)
        self.total_easy_seconds += (total_rest_meters * easy_run_pace)
        self.total_hard_seconds += (total_hard_meters * tempo_run_pace)

        return workout

    def gen_threshold_run(self, threshold_run_pace, easy_run_pace, max_run_distance):
        """Utility function for creating a threshold workout."""
        pass

    def gen_speed_run(self, short_interval_run_pace, speed_run_pace, easy_run_pace, goal_distance):
        """Utility function for creating a speed/interval workout."""

        # Constants.
        MIN_REPS_INDEX = 0
        MAX_REPS_INDEX = 1
        REP_DISTANCE_INDEX = 2

        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Build a collection of possible run interval sessions, sorted by target distance. Order is { min reps, max reps, distance in meters }.
        possible_workouts = [ [ 4, 8, 100 ], [ 4, 8, 200 ], [ 4, 8, 400 ], [ 4, 8, 600 ], [ 2, 8, 800 ], [ 2, 6, 1000 ], [ 2, 4, 1600 ] ]

        # Build a probability density function for selecting the workout. Longer goals should tend towards longer intervals and so on.
        num_possible_workouts = len(possible_workouts)
        x = np.arange(0, num_possible_workouts, 1)
        center_index = int(num_possible_workouts / 2)
        densities = norm.pdf(x, loc=center_index)

        # Make sure the densities array adds up to one.
        total_densities = sum(densities)
        if total_densities < 1.0:
            densities[center_index] += (1.0 - total_densities)

        # If the goal is less than a 10K then favor the shorter interval workouts. If greater than a 1/2 marathon, favor the longer.
        if goal_distance < 10000:
            mod_densities = np.append(densities[1:len(densities)], densities[0])
        elif goal_distance >= METERS_PER_MARATHON:
            mod_densities = np.append(densities[-1], densities[0:len(densities)-1])
            mod_densities = np.append(densities[-1], densities[0:len(densities)-1])
        elif goal_distance >= METERS_PER_HALF_MARATHON:
            mod_densities = np.append(densities[-1], densities[0:len(densities)-1])
        else:
            mod_densities = densities

        # Select the workout.
        selected_interval_workout_index = np.random.choice(x, p=mod_densities)
        selected_interval_workout = possible_workouts[selected_interval_workout_index]

        # Determine the pace for this workout.
        if selected_interval_workout[REP_DISTANCE_INDEX] < 1000:
            interval_pace = short_interval_run_pace
        else:
            interval_pace = speed_run_pace

        # Determine the number of reps for this workout.
        selected_reps = np.random.choice(range(selected_interval_workout[MIN_REPS_INDEX], selected_interval_workout[MAX_REPS_INDEX], 2))

        # Fetch the distance for this workout.
        interval_distance = selected_interval_workout[REP_DISTANCE_INDEX]

        # Determine the rest interval distance. This will be some multiplier of the interval.
        rest_interval_distance = interval_distance * np.random.choice([1, 1.5, 2])

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_RUN, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_interval(selected_reps, interval_distance, interval_pace, rest_interval_distance, easy_run_pace)
        workout.add_cooldown(cooldown_duration)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        total_rest_meters = ((selected_reps - 1) * rest_interval_distance)
        total_hard_meters = (selected_reps * interval_distance)
        self.easy_distance_total_meters += (warmup_duration / easy_run_pace)
        self.easy_distance_total_meters += (cooldown_duration / easy_run_pace)
        self.easy_distance_total_meters += (total_rest_meters)
        self.hard_distance_total_meters += (total_hard_meters)

        # Tally up the easy and hard seconds.
        self.total_easy_seconds += (warmup_duration + cooldown_duration)
        self.total_easy_seconds += (total_rest_meters * easy_run_pace)
        self.total_hard_seconds += (total_hard_meters * interval_pace)

        return workout

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
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_LONG_RUN, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_interval(1, interval_distance_meters, long_run_pace, 0, 0)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += interval_distance_meters

        # Tally up the easy and hard seconds.
        self.total_easy_seconds += interval_distance_meters * long_run_pace

        return workout

    def gen_free_run(self):
        """Utility function for creating a free run workout."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(3000, 10000)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_FREE_RUN, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_interval(1, interval_distance_meters, 0, 0, 0)

        # Tally up the easy and hard distance so we can keep the weekly plan in check.
        self.easy_distance_total_meters += interval_distance_meters

        return workout

    def gen_hill_repeats(self):
        """Utility function for creating a hill session."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(3000, 7000)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_HILL_REPEATS, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_interval(1, interval_distance_meters, 0, 0, 0)

        return workout

    def gen_fartlek_run(self):
        """Utility function for creating a fartlek session."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(3000, 10000)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_FARTLEK_RUN, self.user_id)
        workout.sport_type = Keys.TYPE_RUNNING_KEY
        workout.add_interval(1, interval_distance_meters, 0, 0, 0)

        return workout

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
        num_runs = inputs[Keys.NUM_RUNS_LAST_FOUR_WEEKS]
        exp_level = inputs[Keys.EXPERIENCE_LEVEL_KEY]
        comfort_level = inputs[Keys.STRUCTURED_TRAINING_COMFORT_LEVEL_KEY]

        # Handle situation in which the user hasn't run in four weeks.
        if not RunPlanGenerator.valid_float(longest_run_in_four_weeks):
            workouts.append(self.gen_free_run())
            workouts.append(self.gen_free_run())
            return workouts
        
        # Handle situation in which the user hasn't run *much* in the last four weeks.
        if num_runs is None or num_runs < 4:
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
        if exp_level <= 5:
            max_easy_run_distance = longest_run_in_four_weeks * 0.60
            max_tempo_run_distance = longest_run_in_four_weeks * 0.40
        else:
            max_easy_run_distance = longest_run_in_four_weeks * 0.75
            max_tempo_run_distance = longest_run_in_four_weeks * 0.50

        # Don't make any runs (other than intervals, tempo runs, etc.) shorter than this.
        min_run_distance = avg_run_distance * 0.5
        if min_run_distance > max_easy_run_distance:
            min_run_distance = max_easy_run_distance

        # We'll also set the percentage of easy miles/kms based on the experience level.
        if exp_level <= 5:
            min_easy_distance_percentage = 0.90
        elif exp_level <= 7:
            min_easy_distance_percentage = 0.80
        else:
            min_easy_distance_percentage = 0.75

        iter_count = 0
        done = False
        while not done:

            workouts = []

            # Keep track of the number of easy miles/kms and the number of hard miles/kms we're expecting the user to run so we can balance the two.
            self.easy_distance_total_meters = 0.0
            self.hard_distance_total_meters = 0.0
            self.total_easy_seconds = 0.0
            self.total_hard_seconds = 0.0

            # Add a long run.
            long_run_workout = self.gen_long_run(long_run_pace, longest_run_in_four_weeks, min_run_distance, max_long_run_distance)
            workouts.append(long_run_workout)

            # Add an easy run.
            easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
            workouts.append(easy_run_workout)

            # Add a tempo run. Run should be 20-30 minutes in duration.
            tempo_run_workout = self.gen_tempo_run(tempo_run_pace, easy_run_pace, max_tempo_run_distance)
            workouts.append(tempo_run_workout)

            # The user cares about speed as well as completing the distance. Also note that we should add strikes to one of the other workouts.
            if goal_type.lower() == Keys.GOAL_TYPE_SPEED.lower():

                # Add an interval/speed session.
                interval_workout = self.gen_speed_run(short_interval_run_pace, speed_run_pace, easy_run_pace, goal_distance)
                workouts.append(interval_workout)

            # Add an easy run.
            easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
            workouts.append(easy_run_workout)

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
            workout.calculate_estimated_strain_score(functional_threshold_pace)

        return workouts
