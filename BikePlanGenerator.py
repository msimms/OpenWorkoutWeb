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

    def gen_interval_session(self, goal_distance):
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

        # If the goal is less than a 10K then favor the shorter interval workouts. If greater than a 1/2 marathon, favor the longer.
        if goal_distance < 40000:
            mod_densities = np.append(densities[1:len(densities)], densities[0])
        else:
            mod_densities = densities

        # Select the workout.
        selected_interval_workout_index = np.random.choice(x, p=mod_densities)
        selected_interval_workout = possible_workouts[selected_interval_workout_index]

        # Fetch the details for this workout.
        interval_reps = selected_interval_workout[0]
        interval_seconds = selected_interval_workout[1]
        interval_power = selected_interval_workout[2]
        rest_seconds = interval_seconds / 2

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_INTERVAL_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_time_and_power_interval(interval_reps, interval_seconds, interval_power, rest_seconds, 0.4)
        workout.add_cooldown(cooldown_duration)

        return workout

    def gen_easy_aerobic_ride(self, goal_distance, longest_ride_in_four_weeks, avg_bike_duration):
        """Utility function for creating an easy ride, basically an aerobic or base mileage ride."""
        """Aerobic rides are typically around 55-75% FTP."""

        # Sanity check
        if avg_bike_duration < 1800:
            avg_bike_duration = 1800

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_time_and_power_interval(1, avg_bike_duration, 60.0, 0, 0)

        return workout

    def gen_tempo_ride(self):
        """Utility function for creating a tempo ride."""
        """Tempo rides are typically around 75-85% FTP."""

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        num_interval_seconds = random.randint(2, 4) * 5 * 60
        workout.add_time_and_power_interval(random.randint(2, 4), num_interval_seconds, 80.0, num_interval_seconds / 2, 0.4)
        workout.add_cooldown(cooldown_duration)

        # 3 min at goal race pace with 3 minutes recovery.

        return workout

    def gen_sweet_spot_ride(self):
        """Utility function for creating a sweet spot ride."""
        """Sweet spot rides are typically around 85-95% FTP."""

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SWEET_SPOT_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        num_interval_seconds = random.randint(2, 4) * 5 * 60
        workout.add_time_and_power_interval(random.randint(2, 4), num_interval_seconds, 90.0, num_interval_seconds / 2, 0.4)
        workout.add_cooldown(cooldown_duration)

        return workout

    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # Extract the necessary inputs.
        goal_distance = inputs[Keys.GOAL_BIKE_DISTANCE_KEY]
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        goal_type = inputs[Keys.GOAL_TYPE_KEY]
        weeks_until_goal = inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY]
        longest_ride_week_1 = inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_1_KEY] # Most recent week
        longest_ride_week_2 = inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_2_KEY]
        longest_ride_week_3 = inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_3_KEY]
        longest_ride_week_4 = inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_4_KEY]
        avg_bike_duration = inputs[Keys.PLAN_INPUT_AVG_CYCLING_DURATION_IN_FOUR_WEEKS]
        has_bicycle = inputs[Keys.USER_HAS_BICYCLE]

        # The user doesn't have a bicycle, so return.
        if not has_bicycle:
            return workouts

        # Longest ride in four weeks.
        longest_ride_in_four_weeks = max([longest_ride_week_1, longest_ride_week_2, longest_ride_week_3, longest_ride_week_4])

        # Are we in a taper?
        in_taper = self.is_in_taper(weeks_until_goal, goal)

        # Add critical workouts:
        # Long ride, culminating in (maybe) an overdistance ride.

        # General fitness
        if goal == Keys.GOAL_FITNESS_KEY:
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            workouts.append(self.gen_interval_session(goal_distance))

        # Cross training to support medium distance running
        elif goal == Keys.GOAL_5K_RUN_KEY or goal == Keys.GOAL_10K_RUN_KEY or goal == Keys.GOAL_15K_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))

        # Cross training to support long distance running
        elif goal == Keys.GOAL_HALF_MARATHON_RUN_KEY or goal == Keys.GOAL_MARATHON_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))

        # Cross training to support ultra distance running
        elif goal == Keys.GOAL_50K_RUN_KEY or goal == Keys.GOAL_50_MILE_RUN_KEY:
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))

        # Short distance triathlons
        elif goal == Keys.GOAL_SPRINT_TRIATHLON_KEY or goal == Keys.GOAL_OLYMPIC_TRIATHLON_KEY:
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            if in_taper or goal_type == Keys.GOAL_TYPE_COMPLETION:
                workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            else:
                workouts.append(self.gen_interval_session(goal_distance))

        # Long distance triathlons
        elif goal == Keys.GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY or goal == Keys.GOAL_IRON_DISTANCE_TRIATHLON_KEY:
            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            if in_taper or goal_type == Keys.GOAL_TYPE_COMPLETION:
                workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            else:
                workouts.append(self.gen_interval_session(goal_distance))

        return workouts
