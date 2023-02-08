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

    @staticmethod
    def round_distance(number, nearest):
        return nearest * round(number / nearest)

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

    def gen_cadence_drills(self):
        """Utility function for creating a workout emphasizing cadence."""
        """Note: Haven't implemented this, because it only seems to have beneft if the cyclist is not doing strenght work."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_BIKE_CADENCE_DRILLS, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY

        return workout

    def gen_interval_session(self, goal_distance):
        """Utility function for creating an interval workout."""
        MIN_SETS_INDEX = 0
        MAX_SETS_INDEX = 1
        NUM_REPS_INDEX = 2
        SECONDS_HARD_INDEX = 3
        SECONDS_EASY_INDEX = 4
        PERCENTAGE_FTP_INDEX = 5

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Notes:
        # 3-4 minute rests between blocks
        # 2-4 blocks, based on experience

        # Ronnestad Intervals
        # 3x (13x (30 seconds hard / 15 seconds easy))

        # 30:30s
        # 2-4x (30 seconds hard / 30 seconds easy)

        # 40:20s
        # 2-4x (40 seconds hard / 20 seconds easy)

        # Tabata Intervals
        # 2-4x (10x (30 seconds hard / 20 seconds easy))

        # V02 Max Intervals
        # 8x (2 minutes hard / 2 min easy)
        # 6x (3 minutes hard / 2-3 min easy)
        # 5x (4 minutes hard / 2-3 min easy)

        # Longer intervals for sustained power
        # 4x8 minutes hard / 2-4 min easy

    	# Build a collection of possible bike interval sessions, sorted by target time.
        # Order is { min sets, max sets, num reps, seconds hard, seconds easy, percentage of threshold power }.
        possible_workouts = [ [ 1, 3, 13, 30, 15, 170 ],
                              [ 2, 4, 1, 30, 30, 170 ],
                              [ 2, 4, 1, 40, 20, 170 ],
                              [ 2, 4, 10, 30, 20, 170 ],
                              [ 1, 1, 8, 120, 120, 140 ],
                              [ 1, 1, 6, 180, 150, 130 ],
                              [ 1, 1, 5, 240, 150, 120 ],
                              [ 1, 1, 4, 480, 180, 120 ] ]

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
        min_sets = selected_interval_workout[MIN_SETS_INDEX]
        max_sets = selected_interval_workout[MAX_SETS_INDEX]
        num_sets = random.randint(min_sets, max_sets)
        num_reps = selected_interval_workout[NUM_REPS_INDEX]
        interval_seconds = selected_interval_workout[SECONDS_HARD_INDEX]
        interval_rest = selected_interval_workout[SECONDS_EASY_INDEX]
        interval_power = selected_interval_workout[PERCENTAGE_FTP_INDEX]

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_INTERVAL_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        for i in range(0, num_sets):
            workout.add_time_and_power_interval(num_reps, interval_seconds, interval_power, interval_rest, 0.4)
            if i < num_sets - 1:
                workout.add_time_and_power_interval(1, 120, 0.4, 0, 0)
        workout.add_cooldown(cooldown_duration)

        return workout

    def gen_easy_aerobic_ride(self, goal_distance, longest_ride_in_four_weeks, avg_bike_duration):
        """Utility function for creating an easy ride, basically an aerobic or base mileage ride."""
        """Aerobic rides are typically around 55-75% FTP."""

        # Sanity check
        if avg_bike_duration < 1800:
            avg_bike_duration = 1800

		# Select the power (% of FTP). Round to the nearest 5 watts.
        interval_power = random.randint(55, 75)
        interval_power = BikePlanGenerator.round_distance(interval_power, 5)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_time_and_power_interval(1, avg_bike_duration, interval_power, 0, 0)

        return workout

    def gen_tempo_ride(self):
        """Utility function for creating a tempo ride."""
        """Tempo rides are typically around 75-85% FTP."""

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

		# Select the power (% of FTP). Round to the nearest 5 watts.
        interval_power = random.randint(75, 85)
        interval_power = BikePlanGenerator.round_distance(interval_power, 5)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        num_interval_seconds = random.randint(2, 4) * 5 * 60
        workout.add_time_and_power_interval(random.randint(2, 4), num_interval_seconds, interval_power, num_interval_seconds / 2, 0.4)
        workout.add_cooldown(cooldown_duration)

        # 3 min at goal race pace with 3 minutes recovery.

        return workout

    def gen_sweet_spot_ride(self):
        """Utility function for creating a sweet spot ride."""
        """Sweet spot rides are typically around 85-95% FTP."""

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

		# Select the power (% of FTP). Round to the nearest 5 watts.
        interval_power = random.randint(85, 95)
        interval_power = BikePlanGenerator.round_distance(interval_power, 5)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SWEET_SPOT_RIDE, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.add_warmup(warmup_duration)
        num_interval_seconds = random.randint(2, 4) * 5 * 60
        workout.add_time_and_power_interval(random.randint(2, 4), num_interval_seconds, interval_power, num_interval_seconds / 2, 0.4)
        workout.add_cooldown(cooldown_duration)

        return workout

    def gen_goal_workout(self, goal_distance_meters, goal_date):
        """Utility function for creating the goal workout/race."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EVENT, self.user_id)
        workout.sport_type = Keys.TYPE_CYCLING_KEY
        workout.scheduled_time = goal_date
        workout.add_distance_interval(1, goal_distance_meters, 0, 0, 0)

        return workout

    def gen_workouts_for_next_week(self, inputs, easy_week, in_taper):
        """Generates the workouts for the next week, but doesn't schedule them."""
        """easy_week indicates whether or not this is the end of a training block."""
        """in_taper indicates whether or not we're in the pre-event taper."""

        workouts = []

        # Extract the necessary inputs.
        goal_distance = inputs[Keys.GOAL_BIKE_DISTANCE_KEY]
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        goal_type = inputs[Keys.GOAL_TYPE_KEY]
        goal_date = inputs[Keys.PLAN_INPUT_GOAL_DATE_KEY]
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

        # Add critical workouts:
        # Long ride, culminating in (maybe) an overdistance ride.

        # General fitness.
        if goal == Keys.GOAL_FITNESS_KEY:

            workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
            workouts.append(self.gen_interval_session(goal_distance))

        else:

            # Is this the goal week? If so, add that event.
            if self.is_goal_week(goal, weeks_until_goal, goal_distance):
                goal_workout = self.gen_goal_workout(goal_distance, goal_date)
                workouts.append(goal_workout)

            # Cross training to support medium distance running
            if goal == Keys.GOAL_5K_RUN_KEY or goal == Keys.GOAL_10K_RUN_KEY or goal == Keys.GOAL_15K_RUN_KEY:
                workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))
                workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))

            # Cross training to support long distance running
            elif (goal == Keys.GOAL_HALF_MARATHON_RUN_KEY or goal == Keys.GOAL_MARATHON_RUN_KEY) and not in_taper:
                workouts.append(self.gen_easy_aerobic_ride(goal_distance, longest_ride_in_four_weeks, avg_bike_duration))

            # Cross training to support ultra distance running
            elif (goal == Keys.GOAL_50K_RUN_KEY or goal == Keys.GOAL_50_MILE_RUN_KEY) and not in_taper:
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
