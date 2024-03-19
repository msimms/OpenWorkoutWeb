# Copyright 2019 Michael J Simms
"""Generates a run plan for the specifiied user."""

import datetime
import math
import numpy as np
import random
from scipy.stats import norm

import Keys
import PlanGenerator
import Units
import WorkoutFactory

INTENSITY_ZONE_INDEX_LOW = 0
INTENSITY_ZONE_INDEX_MED = 1
INTENSITY_ZONE_INDEX_HIGH = 2

class RunPlanGenerator(PlanGenerator.PlanGenerator):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id, training_philosophy):
        """Constructor"""
        self.user_id = user_id

        # Time below cutoff_pace_1 counts towards the first bucket.
        # Time between cutoff_pace_1 and cutoff_pace_2 counts towards the second bucket.
        # Time above cutoff_pace_2 counts towards the third bucket.
        self.cutoff_pace_1 = 0.0
        self.cutoff_pace_2 = 0.0

        # The training philosophy indicates how much time we intended
        # to spend in each training zone.
        if training_philosophy == Keys.TRAINING_PHILOSOPHY_THRESHOLD:
            self.training_zone_distribution = Keys.TID_THRESHOLD
        elif training_philosophy == Keys.TRAINING_PHILOSOPHY_POLARIZED:
            self.training_zone_distribution = Keys.TID_POLARIZED
        elif training_philosophy == Keys.TRAINING_PHILOSOPHY_PYRAMIDAL:
            self.training_zone_distribution = Keys.TID_PYRAMIDAL
        else:
            self.training_zone_distribution = Keys.TID_POLARIZED

        self.clear_intensity_distribution()

    def max_long_run_distance(self, goal_distance):
        """If the goal distance is a marathon then the longest run should be somewhere between 18 and 22 miles."""
        """The equation was derived by playing with trendlines in a spreadsheet."""
        return ((-0.002 * goal_distance) * (-0.002 * goal_distance)) + (0.7 * goal_distance) + 4.4

    def max_attainable_distance(self, base_distance_meters, num_weeks):
        """Assume the athlete can improve by 10%/week in maximum distance."""

        # To keep the calculation from going out of range, scale the input from meters to kms.
        base_distance_kms = base_distance_meters / 1000.0

        # Assume the athlete can run at least two kilometers.
        if base_distance_kms < 2.0:
            base_distance_kms = 2.0

        # The calculation is basically the same as for compound interest.
        # Be sure to scale back up to meters.
        weekly_rate = 0.1
        return (base_distance_kms + ((base_distance_kms * (1.0 + (weekly_rate / 52.0))**(52.0 * num_weeks)) - base_distance_kms)) * 1000.0

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""

        # Inputs.
        goal_distance = inputs[Keys.GOAL_RUN_DISTANCE_KEY]
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        weeks_until_goal = inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY]
        longest_run_week_1 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY]
        longest_run_week_2 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY]
        longest_run_week_3 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY]
        longest_run_week_4 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY]
        longest_run_in_four_weeks = max([longest_run_week_1, longest_run_week_2, longest_run_week_3, longest_run_week_4])

        # The user does not have a race goal.
        if goal == Keys.GOAL_FITNESS_KEY:
            return True

        # The user can already do the distance.
        distance_to_goal = goal_distance - longest_run_in_four_weeks
        if distance_to_goal < 0.0:
            return True

        # Too late. The user should be in the taper.
        should_be_in_taper = PlanGenerator.PlanGenerator.is_in_taper(weeks_until_goal, goal)
        if should_be_in_taper:
            return False

        # Can we get to the target distance, or close to it, in the time remaining.
        max_distance_needed = self.max_long_run_distance(goal_distance)
        max_attainable_distance = self.max_attainable_distance(longest_run_in_four_weeks, weeks_until_goal)
        if max_attainable_distance < 0.1: # Sanity check
            return False
        return max_attainable_distance >= max_distance_needed

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

    def clear_intensity_distribution(self):
        """Resets all intensity distribution tracking variables."""

        # Distribution of the number of workouts in each intensity zone.
        # 0 index is least intense.
        self.intensity_distribution_workouts = []
        self.intensity_distribution_workouts.append(0)
        self.intensity_distribution_workouts.append(0)
        self.intensity_distribution_workouts.append(0)

    def check_intensity_distribution(self):
        """How far is this workout plan from the ideal intensity distribution?"""
        total_workouts = sum(self.intensity_distribution_workouts)
        intensity_distribution_percent = [(x / total_workouts) * 100.0 for x in self.intensity_distribution_workouts]
        intensity_distribution_score = sum([abs(x - y) for x, y in zip(intensity_distribution_percent, self.training_zone_distribution)])
        return intensity_distribution_score

    def gen_easy_run(self, pace, min_run_distance, max_run_distance):
        """Utility function for creating an easy run of some random distance between min and max."""

        # An easy run needs to be at least a couple of kilometers.
        if min_run_distance < 3000:
            min_run_distance = 3000
        if max_run_distance < 3000:
            max_run_distance = 3000

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(min_run_distance, max_run_distance)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EASY_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_distance_interval(1, interval_distance_meters, pace, 0, 0)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_LOW] += 1

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

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TEMPO_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_distance_interval(num_intervals, interval_distance_meters, tempo_run_pace, 0, easy_run_pace)
        workout.add_cooldown(cooldown_duration)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_MED] += 1

        return workout

    def gen_threshold_run(self, threshold_run_pace, easy_run_pace, max_run_distance):
        """Utility function for creating a threshold workout."""

        # Decide on the number of intervals and their distance.
        temp_distance = 20.0 * threshold_run_pace
        interval_distance_meters = RunPlanGenerator.nearest_interval_distance(temp_distance, 2000.0)

        # Sanity check.
        if interval_distance_meters > max_run_distance:
            interval_distance_meters = max_run_distance
        if interval_distance_meters < 1000:
            interval_distance_meters = 1000

        # Warmup and cooldown duration.
        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_THRESHOLD_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_distance_interval(1, interval_distance_meters, threshold_run_pace, 0, 0)
        workout.add_cooldown(cooldown_duration)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_HIGH] += 1

        return workout

    def gen_norwegian_intervals(self, threshold_run_pace, easy_run_pace):
        """4x4 minutes fast with 3 minutes easy jog"""

        warmup_duration = 10 * 60 # Ten minute warmup
        cooldown_duration = 10 * 60 # Ten minute cooldown

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_SPEED_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_time_interval(4, 4 * 60, threshold_run_pace, 3 * 60, easy_run_pace)
        workout.add_cooldown(cooldown_duration)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_HIGH] += 1

        return workout

    def gen_interval_session(self, short_interval_run_pace, speed_run_pace, easy_run_pace, goal_distance):
        """Utility function for creating a speed/interval workout."""

        # Constants.
        MIN_REPS_INDEX = 0
        MAX_REPS_INDEX = 1
        REP_DISTANCE_INDEX = 2

        # Warmup and cooldown duration.
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
        elif goal_distance >= Units.METERS_PER_MARATHON:
            mod_densities = np.append(densities[-1], densities[0:len(densities)-1])
            mod_densities = np.append(densities[-1], densities[0:len(densities)-1])
        elif goal_distance >= Units.METERS_PER_HALF_MARATHON:
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
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_warmup(warmup_duration)
        workout.add_distance_interval(selected_reps, interval_distance, interval_pace, rest_interval_distance, easy_run_pace)
        workout.add_cooldown(cooldown_duration)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_HIGH] += 1

        return workout

    def gen_long_run(self, long_run_pace, longest_run_in_four_weeks, min_run_distance, max_run_distance):
        """Utility function for creating a long run workout."""

        # Long run should be 10% longer than the previous long run, within the bounds provided by min and max.
        # No matter what, it should be at least 5K.
        long_run_distance = longest_run_in_four_weeks * 1.1
        if long_run_distance > max_run_distance:
            long_run_distance = max_run_distance
        if long_run_distance < min_run_distance:
            long_run_distance = min_run_distance
        if long_run_distance < 5000:
            long_run_distance = 5000
        interval_distance_meters = RunPlanGenerator.round_distance(long_run_distance)

        # Consider long runs closer to the event, with either a race pace effort at the end
        # or a 5K repeats alternating between easy and race pace.

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_LONG_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_distance_interval(1, interval_distance_meters, long_run_pace, 0, 0)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_LOW] += 1

        return workout

    def gen_free_run(self):
        """Utility function for creating a free run workout."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(3000, 10000)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_FREE_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_distance_interval(1, interval_distance_meters, 0, 0, 0)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_LOW] += 1

        return workout

    def gen_hill_repeats(self):
        """Utility function for creating a hill session."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(3000, 10000)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_HILL_REPEATS, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_distance_interval(1, interval_distance_meters, 0, 0, 0)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_MED] += 1

        return workout

    def gen_fartlek_run(self):
        """Utility function for creating a fartlek session."""

        # Roll the dice to figure out the distance.
        run_distance = random.uniform(3000, 10000)
        interval_distance_meters = round(run_distance, -3)

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_FARTLEK_RUN, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.add_distance_interval(1, interval_distance_meters, 0, 0, 0)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_HIGH] += 1

        return workout

    def gen_goal_workout(self, goal_distance_meters, goal_date):
        """Utility function for creating the goal workout/race."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_EVENT, self.user_id)
        workout.activity_type = Keys.TYPE_RUNNING_KEY
        workout.scheduled_time = datetime.datetime.fromtimestamp(goal_date)
        workout.add_distance_interval(1, goal_distance_meters, 0, 0, 0)

        # Update the tally of easy, medium, and hard workouts so we can keep the weekly plan in check.
        self.intensity_distribution_workouts[INTENSITY_ZONE_INDEX_HIGH] += 1

        return workout

    def max_taper_distance(self, race_distance):
        """Returns the maximum distance for a single run during the taper."""
        if race_distance == Keys.GOAL_5K_RUN_KEY:
            return 5000
        if race_distance == Keys.GOAL_10K_RUN_KEY:
            return 10000
        if race_distance == Keys.GOAL_15K_RUN_KEY:
            return 0.9 * 15000
        if race_distance == Keys.GOAL_HALF_MARATHON_RUN_KEY:
            return 0.75 * Units.METERS_PER_HALF_MARATHON
        if race_distance == Keys.GOAL_MARATHON_RUN_KEY:
            return Units.METERS_PER_HALF_MARATHON
        if race_distance == Keys.GOAL_50K_RUN_KEY:
            return Units.METERS_PER_HALF_MARATHON
        if race_distance == Keys.GOAL_50_MILE_RUN_KEY:
            return Units.METERS_PER_HALF_MARATHON
        if race_distance == Keys.GOAL_SPRINT_TRIATHLON_KEY:
            return 5000
        if race_distance == Keys.GOAL_OLYMPIC_TRIATHLON_KEY:
            return 10000
        if race_distance == Keys.GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY:
            return 0.75 * Units.METERS_PER_HALF_MARATHON
        if race_distance == Keys.GOAL_IRON_DISTANCE_TRIATHLON_KEY:
            return Units.METERS_PER_HALF_MARATHON
        return Units.METERS_PER_HALF_MARATHON

    def gen_workouts_for_next_week_fitness_goal(self, inputs):
        """Generates run workouts for the next week if the user's goal is simple fitness."""
        workouts = []

        # Extract the necessary inputs.
        easy_run_pace = inputs[Keys.EASY_RUN_PACE]
        longest_run_week_1 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY] # Most recent week
        longest_run_week_2 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY]
        longest_run_week_3 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY]
        longest_run_week_4 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY]

        # Longest run in four weeks.
        longest_run_in_four_weeks = max([longest_run_week_1, longest_run_week_2, longest_run_week_3, longest_run_week_4])

        # Handle situation in which the user hasn't run in four weeks.
        if not PlanGenerator.PlanGenerator.valid_float(longest_run_in_four_weeks) or longest_run_in_four_weeks < 1.0:
            workouts.append(self.gen_free_run())
            workouts.append(self.gen_free_run())
            workouts.append(self.gen_free_run())
        else:
            workouts.append(self.gen_easy_run(easy_run_pace, 3000, 5000))
            workouts.append(self.gen_easy_run(easy_run_pace, 3000, 5000))
            workouts.append(self.gen_easy_run(easy_run_pace, 3000, 8000))
        return workouts

    def gen_workouts_for_next_week_event_goal(self, inputs, easy_week, in_taper):
        """Generates run workouts for the next week if the user is targeting an event."""
        workouts = []
        best_workouts = []
        best_intensity_distribution_score = None

        # 3 Critical runs: Speed session, tempo or threshold run, and long run

        # Extract the necessary inputs.
        goal_distance = inputs[Keys.GOAL_RUN_DISTANCE_KEY]
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        goal_type = inputs[Keys.PLAN_INPUT_GOAL_TYPE_KEY]
        goal_date = inputs[Keys.PLAN_INPUT_GOAL_DATE_KEY]
        weeks_until_goal = inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY]
        short_interval_run_pace = inputs[Keys.SHORT_INTERVAL_RUN_PACE]
        functional_threshold_pace = inputs[Keys.FUNCTIONAL_THRESHOLD_PACE]
        speed_run_pace = inputs[Keys.SPEED_RUN_PACE]
        tempo_run_pace = inputs[Keys.TEMPO_RUN_PACE]
        long_run_pace = inputs[Keys.LONG_RUN_PACE]
        easy_run_pace = inputs[Keys.EASY_RUN_PACE]
        longest_run_week_1 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY] # Most recent week
        longest_run_week_2 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY]
        longest_run_week_3 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY]
        longest_run_week_4 = inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY]
        total_intensity_week_1 = inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_1_KEY] # Most recent week
        avg_run_distance = inputs[Keys.PLAN_INPUT_AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS]
        num_runs = inputs[Keys.PLAN_INPUT_NUM_RUNS_LAST_FOUR_WEEKS]
        avg_num_runs_last_4_weeks = None
        exp_level = inputs[Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY]

        # Longest run in four weeks.
        longest_run_in_four_weeks = max([longest_run_week_1, longest_run_week_2, longest_run_week_3, longest_run_week_4])

        # Handle situation in which the user hasn't run in four weeks.
        if not PlanGenerator.PlanGenerator.valid_float(longest_run_in_four_weeks) or longest_run_in_four_weeks < 1.0:
            workouts.append(self.gen_free_run())
            workouts.append(self.gen_free_run())
            workouts.append(self.gen_free_run())
            return workouts
        
        # No pace data?
        if not (PlanGenerator.PlanGenerator.valid_float(short_interval_run_pace) and \
            PlanGenerator.PlanGenerator.valid_float(speed_run_pace) and \
            PlanGenerator.PlanGenerator.valid_float(tempo_run_pace) and \
            PlanGenerator.PlanGenerator.valid_float(long_run_pace) and \
            PlanGenerator.PlanGenerator.valid_float(easy_run_pace)):
            raise Exception("No run pace data.")

        # Handle situation in which the user hasn't run *much* in the last four weeks.
        if num_runs is None or num_runs < 4:
            workouts.append(self.gen_easy_run(easy_run_pace, 3000, 5000))
            workouts.append(self.gen_easy_run(easy_run_pace, 3000, 5000))
            workouts.append(self.gen_easy_run(easy_run_pace, 3000, 8000))
            return workouts
        else:
            avg_num_runs_last_4_weeks = num_runs / 4

        # If the long run has been increasing for the last three weeks then give the person a break.
        if longest_run_week_1 and longest_run_week_2 and longest_run_week_3 and longest_run_week_4:
            if longest_run_week_1 >= longest_run_week_2 and longest_run_week_2 >= longest_run_week_3 and longest_run_week_3 >= longest_run_week_4:
                longest_run_in_four_weeks *= 0.75

        # Cutoff paces.
        self.cutoff_pace_1 = tempo_run_pace
        self.cutoff_pace_2 = speed_run_pace

        # Compute the longest run needed to accomplish the goal.
        # If the goal distance is a marathon then the longest run should be somewhere between 18 and 22 miles.
        # The non-taper equation was derived by playing with trendlines in a spreadsheet.
        if in_taper:
            max_long_run_distance = self.max_taper_distance(goal_distance)
        else:
            max_distance_needed = self.max_long_run_distance(goal_distance)
            max_attainable_distance = self.max_attainable_distance(longest_run_in_four_weeks, weeks_until_goal)
            stretch_factor = max_attainable_distance / max_distance_needed # Gives us an idea as to how much the user is ahead of schedule.
            if stretch_factor < 1.0:
                stretch_factor = 1.0
            max_long_run_distance = self.max_long_run_distance(goal_distance) * stretch_factor

        # Handle situation in which the user is already meeting or exceeding the goal distance.
        if longest_run_in_four_weeks >= max_long_run_distance:
            longest_run_in_four_weeks = max_long_run_distance

        # Distance ceilings for easy and tempo runs.
        max_easy_run_distance = longest_run_in_four_weeks * 0.90
        max_tempo_run_distance = longest_run_in_four_weeks * 0.50

        # Don't make any runs (other than intervals, tempo runs, etc.) shorter than this.
        min_run_distance = avg_run_distance * 0.5
        if min_run_distance > max_easy_run_distance:
            min_run_distance = max_easy_run_distance

        iter_count = 0
        done = False
        while not done:

            workouts = []

            # Keep track of the number of easy miles/kms and the number of hard miles/kms we're expecting the user to run so we can balance the two.
            self.clear_intensity_distribution()

            # Is this the goal week? If so, add that event.
            if self.is_goal_week(goal, weeks_until_goal, goal_distance):
                goal_workout = self.gen_goal_workout(goal_distance, goal_date)
                workouts.append(goal_workout)

            # Add a long run. No need for a long run if the goal is general fitness.
            if not in_taper:
                long_run_workout = self.gen_long_run(long_run_pace, longest_run_in_four_weeks, min_run_distance, max_long_run_distance)
                workouts.append(long_run_workout)

            # Add an easy run.
            easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
            workouts.append(easy_run_workout)

            # Add a tempo run. Run should be 20-30 minutes in duration.
            tempo_run_workout = self.gen_tempo_run(tempo_run_pace, easy_run_pace, max_tempo_run_distance)
            workouts.append(tempo_run_workout)

            # The user cares about speed as well as completing the distance. Also note that we should add strides to one of the other workouts.
            # We shouldn't schedule any structured speed workouts unless the user is running ~30km/week.
            if goal_type.lower() == Keys.GOAL_TYPE_SPEED.lower() and avg_run_distance >= 30000:

                # Decide which workout we're going to do.
                workout_probability = random.uniform(0, 100)

                # Various types of interval/speed sessions.
                if workout_probability < 10:
                    workout = self.gen_norwegian_intervals(functional_threshold_pace, easy_run_pace)
                elif workout_probability < 50:
                    workout = self.gen_interval_session(short_interval_run_pace, speed_run_pace, easy_run_pace, goal_distance)

                # A fartlek session.
                elif workout_probability < 60:
                    workout = self.gen_fartlek_run()

                # A hill workout session.
                elif workout_probability < 70:
                    workout = self.gen_hill_repeats()

                # A threshold session.
                else:
                    workout = self.gen_threshold_run(functional_threshold_pace, easy_run_pace, goal_distance)

                workouts.append(workout)

            # Add an easy run.
            easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
            workouts.append(easy_run_workout)

            # Is the athlete used to more running? If so, add some more runs.
            if len(workouts) < avg_num_runs_last_4_weeks:
                easy_run_workout = self.gen_easy_run(easy_run_pace, min_run_distance, max_easy_run_distance)
                workouts.append(easy_run_workout)

            # Calculate the total intensity and the intensity for each workout.
            total_intensity = 0.0
            for workout in workouts:
                workout.calculate_estimated_intensity_score_for_running(functional_threshold_pace)
                total_intensity = total_intensity + workout.estimated_intensity_score

            # If this is supposed to be an easy week then the total intensity should be less than last week's intensity.
            # Otherwise, it should be more.
            valid_total_intensity = True
            if total_intensity_week_1 > 0.1: # First week in the training plan won't have any prior data.
                if easy_week:
                    valid_total_intensity = total_intensity < total_intensity_week_1
                else:
                    valid_total_intensity = total_intensity > total_intensity_week_1

            # How far are these workouts from the ideal intensity distribution?
            # Note that we really only care on the second run.
            if best_intensity_distribution_score is None:
                best_intensity_distribution_score = self.check_intensity_distribution()
                best_workouts = workouts
            elif valid_total_intensity:
                intensity_distribution_score = self.check_intensity_distribution()
                if intensity_distribution_score < best_intensity_distribution_score:
                    best_intensity_distribution_score = intensity_distribution_score
                    best_workouts = workouts

            # This is used to make sure we don't loop forever.
            iter_count = iter_count + 1

            # Exit conditions:
            if iter_count >= 6:
                done = True

        return best_workouts

    def gen_workouts_for_next_week(self, inputs, easy_week, in_taper):
        """Generates the workouts for the next week, but doesn't schedule them."""
        """easy_week indicates whether or not this is the end of a training block."""
        """in_taper indicates whether or not we're in the pre-event taper."""

        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]

        # Special case the fitness goal because it's so much simpler.
        if goal == Keys.GOAL_FITNESS_KEY:
            return self.gen_workouts_for_next_week_fitness_goal(inputs)
        return self.gen_workouts_for_next_week_event_goal(inputs, easy_week, in_taper)
