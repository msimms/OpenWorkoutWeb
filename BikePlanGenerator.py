# Copyright 2019 Michael J Simms
"""Generates a bike plan for the specifiied user."""

import numpy as np
import random
from scipy.stats import norm

import Keys
import PlanGenerator
import WorkoutFactory

class BikePlanGenerator(PlanGenerator.PlanGenerator):
    """Class for generating a bike plan for the specifiied user."""

    def __init__(self, user_id, training_philosophy):
        self.user_id = user_id

        # The training philosophy indicates how much time we intended
        # to spend in each training zone.
        if training_philosophy == Keys.TRAINING_PHILOSOPHY_THRESHOLD:
            self.training_philosophy = Keys.TID_THRESHOLD
        elif training_philosophy == Keys.TRAINING_PHILOSOPHY_POLARIZED:
            self.training_philosophy = Keys.TID_POLARIZED
        elif training_philosophy == Keys.TRAINING_PHILOSOPHY_PYRAMIDAL:
            self.training_philosophy = Keys.TID_PYRAMIDAL
        else:
            self.training_philosophy = Keys.TID_POLARIZED

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""

        # If we're not planning to do any cycling then of course it's possible.
        goal_distance = inputs[Keys.GOAL_BIKE_DISTANCE_KEY]
        if goal_distance < 0.1:
            return True

        has_bicycle = inputs[Keys.USER_HAS_BICYCLE]
        return has_bicycle

    def gen_hill_ride(self):
        """Utility function for creating a hill workout."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_HILL_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY

        return workout

    def gen_interval_session(self, goal_distance, threshold_power):
        """Utility function for creating an interval workout."""

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Tabata Intervals
        # 10x30 seconds hard / 20 seconds easy

        # V02 Max Intervals
        # 8x2 minutes hard / 2 min easy
        # 6x3 minutes hard / 2-3 min easy
        # 5x4 minutes hard / 2-3 min easy

        # Longer intervals for sustained power
        # 4x8 minutes hard / 2-4 min easy

    	# Build a collection of possible bike interval sessions, sorted by target time. Order is { num reps, seconds hard, percentage of threshold power }.
        possible_workouts = [ [ 10, 30, 170 ], [ 8, 120, 140 ], [ 6, 180, 130 ], [ 5, 240, 120 ], [ 4, 480, 120 ] ]

        # Build a probability density function for selecting the workout. Longer goals should tend towards longer intervals and so on.
        num_possible_workouts = len(possible_workouts)
        x = np.arange(0, num_possible_workouts, 1)
        center_index = int(num_possible_workouts / 2)
        densities = norm.pdf(x, loc=center_index)

        # Make sure the densities array adds up to one.
        total_densities = sum(densities)
        if total_densities < 1.0:
            densities[center_index] += (1.0 - total_densities)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_INTERVAL_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        #workout.add_time_and_power_interval(num_intervals, interval_distance_meters, threshold_power, 0, 0)
        workout.add_cooldown(cooldown_duration)

        return workout

    def gen_tempo_ride(self):
        """Utility function for creating a tempo ride."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY

        # 3 min at goal race pace with 3 minutes recovery.

        return workout

    def gen_easy_aerobic_ride(self):
        """Utility function for creating an easy ride."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY

        return workout

    def gen_sweet_spot_ride(self):
        """Utility function for creating a sweet spot ride."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SWEET_SPOT_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY

        return workout

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # Extract the necessary inputs.
        goal_distance = inputs[Keys.GOAL_BIKE_DISTANCE_KEY]
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        goal_type = inputs[Keys.GOAL_TYPE_KEY]
        weeks_until_goal = inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY]
        avg_bike_distance = inputs[Keys.PLAN_INPUT_AVG_CYCLING_DISTANCE_IN_FOUR_WEEKS]
        has_bicycle = inputs[Keys.USER_HAS_BICYCLE]
        threshold_power = inputs[Keys.THRESHOLD_POWER]

        # The user doesn't have a bicycle, so return.
        if not has_bicycle:
            return workouts

        # Add critical workouts:
        # Long ride, culminating in (maybe) an overdistance ride.

        if goal == Keys.GOAL_FITNESS_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
            workouts.append(self.gen_interval_session(goal_distance, threshold_power))
        elif goal == Keys.GOAL_5K_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_10K_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_15K_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_HALF_MARATHON_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_MARATHON_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_50K_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_50_MILE_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
        elif goal == Keys.GOAL_SPRINT_TRIATHLON_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
            workouts.append(self.gen_interval_session(goal_distance, threshold_power))
        elif goal == Keys.GOAL_OLYMPIC_TRIATHLON_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
            workouts.append(self.gen_interval_session(goal_distance, threshold_power))
        elif goal == Keys.GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
            workouts.append(self.gen_interval_session(goal_distance, threshold_power))
        elif goal == Keys.GOAL_IRON_DISTANCE_TRIATHLON_KEY:
            workouts.append(self.gen_easy_aerobic_ride())
            workouts.append(self.gen_interval_session(goal_distance, threshold_power))

        return workouts
