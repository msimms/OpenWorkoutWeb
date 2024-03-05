# Copyright 2019 Michael J Simms
"""Handles the generation of a workout plan. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import argparse
import datetime
import json
import logging
import os
import pandas
import random
import sys
import time
import traceback
import uuid
import AnalysisScheduler
import BikePlanGenerator
import Config
import DataMgr
import UserMgr
import Keys
import Units
import PlanGenerator
import RunPlanGenerator
import SwimPlanGenerator
import WorkoutScheduler

g_model = None

try:
    import tensorflow as tf
except ModuleNotFoundError:
    pass

class WorkoutPlanGenerator(object):
    """Class for performing the computationally expensive workout plan generation tasks."""

    def __init__(self, config, user_obj):
        self.user_obj = user_obj
        self.data_mgr = DataMgr.DataMgr(config=config, root_url="", analysis_scheduler=AnalysisScheduler.AnalysisScheduler(), import_scheduler=None)
        self.user_mgr = UserMgr.UserMgr(config=config, session_mgr=None)
        super(WorkoutPlanGenerator, self).__init__()

    def log_info(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.info(log_str)

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)
    
    @staticmethod
    def calculate_goal_distances(inputs):
        """Adds the goal distances to the inputs."""
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        goal_lower = goal.lower()

        # Initialize
        inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 0.0
        inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 0.0
        inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 0.0

        # Distances for each event. For general fitness, set goals similar to a sprint tri, depending on available resources.
        if goal_lower == Keys.GOAL_FITNESS_KEY.lower():
            has_swimming_pool_access = inputs[Keys.USER_HAS_SWIMMING_POOL_ACCESS]
            has_bicycle = inputs[Keys.USER_HAS_BICYCLE]

            if has_swimming_pool_access:
                inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 500.0
            if has_bicycle:
                inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 20000.0
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 5000.0
        elif goal_lower == Keys.GOAL_5K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 5000.0
        elif goal_lower == Keys.GOAL_10K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 10000.0
        elif goal_lower == Keys.GOAL_15K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 15000.0
        elif goal_lower == Keys.GOAL_HALF_MARATHON_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = Units.METERS_PER_HALF_MARATHON
        elif goal_lower == Keys.GOAL_MARATHON_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = Units.METERS_PER_MARATHON
        elif goal_lower == Keys.GOAL_50K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 50000.0
        elif goal_lower == Keys.GOAL_50_MILE_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = Units.METERS_PER_50_MILE
        elif goal_lower == Keys.GOAL_SPRINT_TRIATHLON_KEY:
            inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 500.0
            inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 20000.0
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 5000.0
        elif goal_lower == Keys.GOAL_OLYMPIC_TRIATHLON_KEY:
            inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 1500.0
            inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 40000.0
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 10000.0
        elif goal_lower == Keys.GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY:
            inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 1.2 * Units.METERS_PER_MILE
            inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 56.0 * Units.METERS_PER_MILE
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = Units.METERS_PER_HALF_MARATHON
        elif goal_lower == Keys.GOAL_IRON_DISTANCE_TRIATHLON_KEY:
            inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 2.4 * Units.METERS_PER_MILE
            inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 112.0 * Units.METERS_PER_MILE
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = Units.METERS_PER_MARATHON
        elif goal_lower == Keys.GOAL_METRIC_CENTURY_RIDE_KEY:
            inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 0.0
            inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 100000.0
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 0.0
        elif goal_lower == Keys.GOAL_STANDARD_CENTURY_RIDE_KEY:
            inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 0.0
            inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 100.0 * Units.METERS_PER_MILE
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 0.0
        return inputs

    @staticmethod
    def update_summary_data_cb(context, activity, user_id):
        """Callback function for update_summary_data."""
        if Keys.ACTIVITY_SUMMARY_KEY not in activity:
            context.data_mgr.schedule_activity_analysis(activity, user_id)

    def optional_fetch_from_dict(self, dict, key):
        """Utility function for calculate_inputs."""
        if key in dict:
            return dict[key]
        return 0.0

    def optional_fetch_from_dict_with_array(self, dict, key):
        """Utility function for calculate_inputs."""
        if key in dict:
            return dict[key][0]
        return 0.0

    def calculate_inputs(self, user_id):
        """Looks through the user's data and calculates the algorithm's inputs."""

        now = time.time()
        weeks_until_goal = None # Number of weeks until the goal, or None if not applicable
        longest_runs_by_week = [0.0] * 4 # Longest run for each of the recent four weeks
        longest_rides_by_week = [0.0] * 4 # Longest bike rides for each of the recent four weeks
        longest_swims_by_week = [0.0] * 4 # Longest swims for each of the recent four weeks
        run_intensity_by_week = [0.0] * 4 # Total training intensity for each of the recent four weeks
        cycling_intensity_by_week = [0.0] * 4 # Total training intensity for each of the recent four weeks
        swim_intensity_by_week = [0.0] * 4 # Total training intensity for each of the recent four weeks
        running_paces = {}

        # Fetch the details of the user's goal.
        goal, goal_date = self.data_mgr.retrieve_user_goal(user_id)
        if goal is None:
            gen_plan_anyway = self.user_mgr.retrieve_user_setting(user_id, Keys.GEN_WORKOUTS_WHEN_RACE_CAL_IS_EMPTY)
            if gen_plan_anyway:
                goal = Keys.GOAL_FITNESS_KEY
            else:
                raise Exception("A goal has not been defined.")

        # Compute the time remaining until the goal.
        if goal is not Keys.GOAL_FITNESS_KEY:

            # Sanity-check the goal date.
            if goal_date is None:
                raise Exception("A goal date has not been defined.")
            if goal_date <= now:
                raise Exception("The goal date should be in the future.")

            # Convert the goal time into weeks. Round down to the whole week because the schedule is for next week.
            weeks_until_goal = int((goal_date - now) / (7 * 24 * 60 * 60))

        # Is the user interested in just completion, or do they care about performance (i.e. pace/speed)?
        goal_type = self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_TYPE_KEY)

        # Analyze any unanalyzed activities.
        now = time.time()
        num_unanalyzed_activities = self.data_mgr.analyze_unanalyzed_activities(user_id, now - DataMgr.SIX_MONTHS, now)
        if num_unanalyzed_activities > 0:
            raise Exception("Too many unanalyzed activities to generate a workout plan.")

        # This will trigger the callback for each of the user's activities.
        if not self.data_mgr.retrieve_each_user_activity(user_id, self, WorkoutPlanGenerator.update_summary_data_cb, None, None, False):
            raise Exception("Error retrieving the user's activities.")

        #
        # Need cycling FTP and run training paces.
        #

        # Get the user's current estimated cycling FTP.
        threshold_power = self.user_mgr.estimate_ftp(user_id)

        #
        # Need last four weeks averages and bests.
        #

        # Look through the user's four week records.
        _, running_bests, _, cycling_summary_4_week, running_summary_4_week, swimming_summary_4_week = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - DataMgr.FOUR_WEEKS, now)

        # Estimate running paces from the user's four week records.
        if running_bests is not None:
            running_paces = self.data_mgr.compute_run_training_paces(user_id, running_bests)

        #
        # Get some data from the prior four weeks.
        #

        # Most recent week.
        cycling_best_summary, running_best_summary, swimming_best_summary, cycling_week_summary, running_week_summary, swimming_week_summary = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - (DataMgr.ONE_WEEK * 1), now - (DataMgr.ONE_WEEK * 0))
        longest_runs_by_week[0] = self.optional_fetch_from_dict_with_array(running_best_summary, Keys.LONGEST_DISTANCE)
        longest_rides_by_week[0] = self.optional_fetch_from_dict_with_array(cycling_best_summary, Keys.LONGEST_DISTANCE)
        longest_swims_by_week[0] = self.optional_fetch_from_dict_with_array(swimming_best_summary, Keys.LONGEST_DISTANCE)
        run_intensity_by_week[0] = self.optional_fetch_from_dict(running_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        cycling_intensity_by_week[0] = self.optional_fetch_from_dict(cycling_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        swim_intensity_by_week[0] = self.optional_fetch_from_dict(swimming_week_summary, Keys.TOTAL_INTENSITY_SCORE)

        # Two weeks ago.
        cycling_best_summary, running_best_summary, swimming_best_summary, cycling_week_summary, running_week_summary, swimming_week_summary = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - (DataMgr.ONE_WEEK * 2), now - (DataMgr.ONE_WEEK * 1))
        longest_runs_by_week[1] = self.optional_fetch_from_dict_with_array(running_best_summary, Keys.LONGEST_DISTANCE)
        longest_rides_by_week[1] = self.optional_fetch_from_dict_with_array(cycling_best_summary, Keys.LONGEST_DISTANCE)
        longest_swims_by_week[1] = self.optional_fetch_from_dict_with_array(swimming_best_summary, Keys.LONGEST_DISTANCE)
        run_intensity_by_week[1] = self.optional_fetch_from_dict(running_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        cycling_intensity_by_week[1] = self.optional_fetch_from_dict(cycling_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        swim_intensity_by_week[1] = self.optional_fetch_from_dict(swimming_week_summary, Keys.TOTAL_INTENSITY_SCORE)

        # Three weeks ago.
        cycling_best_summary, running_best_summary, swimming_best_summary, cycling_week_summary, running_week_summary, swimming_week_summary = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - (DataMgr.ONE_WEEK * 3), now - (DataMgr.ONE_WEEK * 2))
        longest_runs_by_week[2] = self.optional_fetch_from_dict_with_array(running_best_summary, Keys.LONGEST_DISTANCE)
        longest_rides_by_week[2] = self.optional_fetch_from_dict_with_array(cycling_best_summary, Keys.LONGEST_DISTANCE)
        longest_swims_by_week[2] = self.optional_fetch_from_dict_with_array(swimming_best_summary, Keys.LONGEST_DISTANCE)
        run_intensity_by_week[2] = self.optional_fetch_from_dict(running_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        cycling_intensity_by_week[2] = self.optional_fetch_from_dict(cycling_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        swim_intensity_by_week[2] = self.optional_fetch_from_dict(swimming_week_summary, Keys.TOTAL_INTENSITY_SCORE)

        # Four weeks ago.
        cycling_best_summary, running_best_summary, swimming_best_summary, cycling_week_summary, running_week_summary, swimming_week_summary = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - (DataMgr.ONE_WEEK * 4), now - (DataMgr.ONE_WEEK * 3))
        longest_runs_by_week[3] = self.optional_fetch_from_dict_with_array(running_best_summary, Keys.LONGEST_DISTANCE)
        longest_rides_by_week[3] = self.optional_fetch_from_dict_with_array(cycling_best_summary, Keys.LONGEST_DISTANCE)
        longest_swims_by_week[3] = self.optional_fetch_from_dict_with_array(swimming_best_summary, Keys.LONGEST_DISTANCE)
        run_intensity_by_week[3] = self.optional_fetch_from_dict(running_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        cycling_intensity_by_week[3] = self.optional_fetch_from_dict(cycling_week_summary, Keys.TOTAL_INTENSITY_SCORE)
        swim_intensity_by_week[3] = self.optional_fetch_from_dict(swimming_week_summary, Keys.TOTAL_INTENSITY_SCORE)

        # Compute average running and cycling distances.
        avg_running_distance = 0.0
        avg_cycling_distance = 0.0
        avg_cycling_duration = 0.0
        avg_swimming_distance = 0.0
        num_runs = 0.0
        num_rides = 0.0
        num_swims = 0.0
        if Keys.TOTAL_ACTIVITIES in running_summary_4_week:
            if running_summary_4_week[Keys.TOTAL_ACTIVITIES] > 0:
                num_runs = running_summary_4_week[Keys.TOTAL_ACTIVITIES]
                if Keys.TOTAL_DISTANCE in running_summary_4_week:
                    avg_running_distance = running_summary_4_week[Keys.TOTAL_DISTANCE] / num_runs
        if Keys.TOTAL_ACTIVITIES in cycling_summary_4_week:
            if cycling_summary_4_week[Keys.TOTAL_ACTIVITIES] > 0:
                num_rides = cycling_summary_4_week[Keys.TOTAL_ACTIVITIES]
                if Keys.TOTAL_DISTANCE in cycling_summary_4_week:
                    avg_cycling_distance = cycling_summary_4_week[Keys.TOTAL_DISTANCE] / num_rides
                if Keys.TOTAL_DURATION in cycling_summary_4_week:
                    avg_cycling_duration = cycling_summary_4_week[Keys.TOTAL_DURATION] / num_rides
        if Keys.TOTAL_ACTIVITIES in swimming_summary_4_week:
            if swimming_summary_4_week[Keys.TOTAL_ACTIVITIES] > 0:
                num_swims = swimming_summary_4_week[Keys.TOTAL_ACTIVITIES]
                if Keys.TOTAL_DISTANCE in swimming_summary_4_week:
                    avg_swimming_distance = swimming_summary_4_week[Keys.TOTAL_DISTANCE] / num_swims

        #
        # Need information about the user.
        #

        # Compute the user's age in years.
        birthday = int(self.user_mgr.retrieve_user_setting(user_id, Keys.USER_BIRTHDAY_KEY))
        age_years = (now - birthday) / (365.25 * 24 * 60 * 60)

        # Get the experience/comfort level for the user.
	    # This is meant to give us an idea as to how quickly we can ramp up the intensity.
        experience_level = self.user_mgr.retrieve_user_setting(user_id, Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY)
        comfort_level = self.user_mgr.retrieve_user_setting(user_id, Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY)

        # Store all the inputs in a dictionary.
        inputs = {}
        if len(running_paces) == 0:
            inputs[Keys.SHORT_INTERVAL_RUN_PACE] = None
            inputs[Keys.SPEED_RUN_PACE] = None
            inputs[Keys.TEMPO_RUN_PACE] = None
            inputs[Keys.FUNCTIONAL_THRESHOLD_PACE] = None
            inputs[Keys.LONG_RUN_PACE] = None
            inputs[Keys.EASY_RUN_PACE] = None
        else:
            inputs = running_paces
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY] = longest_runs_by_week[0]
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY] = longest_runs_by_week[1]
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY] = longest_runs_by_week[2]
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY] = longest_runs_by_week[3]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_1_KEY] = longest_rides_by_week[0]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_2_KEY] = longest_rides_by_week[1]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_3_KEY] = longest_rides_by_week[2]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_4_KEY] = longest_rides_by_week[3]
        inputs[Keys.PLAN_INPUT_LONGEST_SWIM_WEEK_1_KEY] = longest_swims_by_week[0]
        inputs[Keys.PLAN_INPUT_LONGEST_SWIM_WEEK_2_KEY] = longest_swims_by_week[1]
        inputs[Keys.PLAN_INPUT_LONGEST_SWIM_WEEK_3_KEY] = longest_swims_by_week[2]
        inputs[Keys.PLAN_INPUT_LONGEST_SWIM_WEEK_4_KEY] = longest_swims_by_week[3]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_1_KEY] = run_intensity_by_week[0] + cycling_intensity_by_week[0] + swim_intensity_by_week[0]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_2_KEY] = run_intensity_by_week[1] + cycling_intensity_by_week[1] + swim_intensity_by_week[1]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_3_KEY] = run_intensity_by_week[2] + cycling_intensity_by_week[2] + swim_intensity_by_week[2]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_4_KEY] = run_intensity_by_week[3] + cycling_intensity_by_week[3] + swim_intensity_by_week[3]
        inputs[Keys.PLAN_INPUT_AGE_YEARS_KEY] = age_years
        inputs[Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY] = experience_level
        inputs[Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY] = comfort_level
        inputs[Keys.PLAN_INPUT_GOAL_KEY] = goal
        inputs[Keys.PLAN_INPUT_GOAL_DATE_KEY] = goal_date
        inputs[Keys.GOAL_TYPE_KEY] = goal_type
        inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY] = weeks_until_goal
        inputs[Keys.PLAN_INPUT_AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS] = avg_running_distance
        inputs[Keys.PLAN_INPUT_AVG_CYCLING_DISTANCE_IN_FOUR_WEEKS] = avg_cycling_distance
        inputs[Keys.PLAN_INPUT_AVG_CYCLING_DURATION_IN_FOUR_WEEKS] = avg_cycling_duration
        inputs[Keys.PLAN_INPUT_AVG_SWIMMING_DISTANCE_IN_FOUR_WEEKS] = avg_swimming_distance
        inputs[Keys.PLAN_INPUT_NUM_RUNS_LAST_FOUR_WEEKS] = num_runs
        inputs[Keys.PLAN_INPUT_NUM_RIDES_LAST_FOUR_WEEKS] = num_rides
        inputs[Keys.PLAN_INPUT_NUM_SWIMS_LAST_FOUR_WEEKS] = num_swims
        inputs[Keys.THRESHOLD_POWER] = threshold_power
        inputs[Keys.USER_HAS_SWIMMING_POOL_ACCESS] = self.user_mgr.retrieve_user_setting(user_id, Keys.USER_HAS_SWIMMING_POOL_ACCESS)
        inputs[Keys.USER_HAS_OPEN_WATER_SWIM_ACCESS] = self.user_mgr.retrieve_user_setting(user_id, Keys.USER_HAS_OPEN_WATER_SWIM_ACCESS)
        inputs[Keys.USER_HAS_BICYCLE] = self.user_mgr.retrieve_user_setting(user_id, Keys.USER_HAS_BICYCLE)

        # Adds the goal distances to the inputs.
        inputs = WorkoutPlanGenerator.calculate_goal_distances(inputs)

        print("Inputs: " + str(inputs))
        return inputs

    def generate_workouts(self, user_id, inputs):
        """Generates workouts for the specified user to perform in the next week."""

        workouts = []

        # Extract the necessary inputs.
        total_intensity_week_1 = inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_1_KEY] # Most recent week
        total_intensity_week_2 = inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_2_KEY]
        total_intensity_week_3 = inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_3_KEY]
        total_intensity_week_4 = inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_4_KEY]
        goal = inputs[Keys.PLAN_INPUT_GOAL_KEY]
        weeks_until_goal = inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY]

        # The training philosophy indicates how much time we intended
        # to spend in each training zone.
        training_philosophy = Keys.TRAINING_PHILOSOPHY_POLARIZED

        # Is it time for an easy week? After four weeks of building we should include an easy week to mark the end of a block.
        easy_week = PlanGenerator.PlanGenerator.is_time_for_an_easy_week(total_intensity_week_1, total_intensity_week_2, total_intensity_week_3, total_intensity_week_4)

        # Are we in the pre-event taper?
        in_taper = PlanGenerator.PlanGenerator.is_in_taper(weeks_until_goal, goal)

        # Generate the swim workouts.
        swim_planner = SwimPlanGenerator.SwimPlanGenerator(user_id)
        if not swim_planner.is_workout_plan_possible(inputs):
            raise Exception("The swim distance goal is not feasible in the time alloted.")
        swim_workouts = swim_planner.gen_workouts_for_next_week(inputs, easy_week, in_taper)
        workouts.extend(swim_workouts)

        # Generate the bike workouts.
        bike_planner = BikePlanGenerator.BikePlanGenerator(user_id, training_philosophy)
        if not bike_planner.is_workout_plan_possible(inputs):
            raise Exception("The bike distance goal is not feasible in the time alloted.")
        bike_workouts = bike_planner.gen_workouts_for_next_week(inputs, easy_week, in_taper)
        workouts.extend(bike_workouts)

        # Generate the run workouts.
        run_planner = RunPlanGenerator.RunPlanGenerator(user_id, training_philosophy)
        if not run_planner.is_workout_plan_possible(inputs):
            raise Exception("The run distance goal is not feasible in the time alloted.")
        run_workouts = run_planner.gen_workouts_for_next_week(inputs, easy_week, in_taper)
        workouts.extend(run_workouts)

        # If the user's goal is only general fitness then make sure we don't have more
        # than seven workouts as they don't need to be doing doubles. In that case,
        # randomly select and remove workouts until we get down to a manageable amount.
        if Keys.PLAN_INPUT_GOAL_KEY in inputs and inputs[Keys.PLAN_INPUT_GOAL_KEY] == Keys.GOAL_FITNESS_KEY:
            while len(workouts) > 7:
                index = int(random.uniform(0, len(workouts)))
                del workouts[index]

        return workouts

    def generate_workouts_using_model(self, user_id, inputs, model):
        """Runs the neural network specified by 'model' to generate the workout plan."""

        # Convert the input dictionary to an array as required by tf.
        model_inputs = [ ]
        model_inputs.append(inputs[Keys.SHORT_INTERVAL_RUN_PACE])
        model_inputs.append(inputs[Keys.SPEED_RUN_PACE])
        model_inputs.append(inputs[Keys.TEMPO_RUN_PACE])
        model_inputs.append(inputs[Keys.FUNCTIONAL_THRESHOLD_PACE])
        model_inputs.append(inputs[Keys.LONG_RUN_PACE])
        model_inputs.append(inputs[Keys.EASY_RUN_PACE])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_1_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_2_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_3_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_4_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_1_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_2_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_3_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_4_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_AGE_YEARS_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_GOAL_KEY])
        model_inputs.append(inputs[Keys.GOAL_TYPE_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY])
        model_inputs.append(inputs[Keys.PLAN_INPUT_AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS])
        model_inputs.append(inputs[Keys.PLAN_INPUT_AVG_CYCLING_DISTANCE_IN_FOUR_WEEKS])
        model_inputs.append(inputs[Keys.PLAN_INPUT_AVG_CYCLING_DURATION_IN_FOUR_WEEKS])
        model_inputs.append(inputs[Keys.PLAN_INPUT_NUM_RUNS_LAST_FOUR_WEEKS])
        model_inputs.append(inputs[Keys.PLAN_INPUT_NUM_RIDES_LAST_FOUR_WEEKS])
        model_inputs.append(inputs[Keys.THRESHOLD_POWER])
        model_inputs.append(inputs[Keys.USER_HAS_SWIMMING_POOL_ACCESS])
        model_inputs.append(inputs[Keys.USER_HAS_OPEN_WATER_SWIM_ACCESS])
        model_inputs.append(inputs[Keys.USER_HAS_BICYCLE])

        workouts = []
        return workouts

    def organize_schedule(self, user_id, workouts):
        """Arranges the user's workouts into days/weeks, etc. To be called after the outputs are generated, but need cleaning up."""

        # What is the first day of next week?
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).date()
        start_time = today + datetime.timedelta(days=7-today.weekday())
        end_time = start_time + datetime.timedelta(days=7)

        # Remove any existing workouts that cover the time period in question.
        if not self.data_mgr.delete_workouts_for_date_range(user_id, start_time, end_time):
            print("Failed to remove old workouts from the database.")

        # Schedule the new workouts.
        scheduler = WorkoutScheduler.WorkoutScheduler(user_id)
        return scheduler.schedule_workouts(workouts, start_time)

    def store_plan(self, user_id, scheduled_workouts):
        """Saves the user's workouts to the database."""
        for scheduled_workout in scheduled_workouts:
            result = self.data_mgr.create_workout(user_id, scheduled_workout)
            if not result:
                print("Failed to save a workout to the database.")

    def generate_plan_for_user(self, model):
        """Entry point for workout plan generation. If a model is not provided then a simpler algorithm is used instead."""

        # Sanity check.
        if self.user_obj is None:
            self.log_error("User information not provided.")
            return []
        if model is None:
            self.log_info("Model not provided. Will use non-ML algorithm instead.")

        workouts = []

        try:
            user_id = self.user_obj[Keys.USER_ID_KEY]

            # When was the last time a plan was generated?

            # Note this attempt to generate a workout plan.
            now = datetime.datetime.utcnow()
            self.user_mgr.update_user_setting(user_id, Keys.USER_PLAN_LAST_GENERATED_TIME, now, now)

            # Compute the model inputs.
            inputs = self.calculate_inputs(user_id)

            # Generate the workouts. If an ML model was provided then use it. Otherwise, use the
            # static logic of the hard-coded "expert" system.
            if model is None:
                workouts = self.generate_workouts(user_id, inputs)
            else:
                workouts = self.generate_workouts_using_model(user_id, inputs, model)

            # Organize the workouts into a schedule.
            scheduled_workouts = self.organize_schedule(user_id, workouts)

            # Save to the database.
            self.store_plan(user_id, scheduled_workouts)
        except:
            self.log_error("Exception when generating a workout plan.")
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return workouts

    def generate_plan_from_inputs(self, model, inputs):
        """Entry point for workout plan generation. If a model is not provided then a simpler algorithm is used instead."""

        # Sanity check.
        if model is None:
            self.log_info("Model not provided. Will use non-ML algorithm instead.")

        workouts = []

        try:
            # Generate the workouts.
            if model is None:
                workouts = self.generate_workouts(None, inputs)
            else:
                workouts = self.generate_workouts_using_model(None, inputs, model)
        except:
            self.log_error("Exception when generating a workout plan.")
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return workouts

def generate_model(training_file_name):
    """Creates the neural network, based on training data from the supplied JSON file."""

    model = None

    with open(training_file_name, 'r') as f:

        # Load the training data from the file.
        datastore = json.load(f)

        # This should give us an array for each piece of training data.
        input_headers = datastore['input_headers']
        input_data = datastore['input_data']
        output_data = datastore['output_data']
        num_inputs = len(input_data)
        num_outputs = len(output_data)
        if num_inputs > 0 and num_outputs > 0:

            # Incorporate the column names for the input data.
            input_columns = []
            input_columns.append(tf.feature_column.numeric_column('metrics'))

            # Transform the input JSON into something we can use in the model.
            dataframe = pandas.DataFrame(input_data)
            train_labels = dataframe.pop('plan_number')
            print("Number of training samples: " + str(len(dataframe)))
            dataset = tf.data.Dataset.from_tensor_slices((dict(dataframe), train_labels))
            dataset = dataset.shuffle(buffer_size=len(dataframe))

            # Build the model.
            model = tf.keras.Sequential([
                tf.keras.layers.DenseFeatures(input_columns),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])

            model.compile(optimizer='adam', loss='binary_crossentropy')
            model.fit(dataset, epochs=5)

        else:
            print("Incomplete training data.")

    return model

def generate_temp_file_name(extension):
    """Utility function for generating a temporary file name."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    tempfile_dir = os.path.join(root_dir, 'tempfile')
    if not os.path.exists(tempfile_dir):
        os.makedirs(tempfile_dir)
    tempfile_dir = os.path.normpath(tempfile_dir)
    tempfile_name = os.path.join(tempfile_dir, str(uuid.uuid4()))
    tempfile_name = tempfile_name + extension
    return tempfile_name

def export_workouts(workouts, format):
    """Writes the workouts to disk in the specified format."""
    for workout in workouts:
        if format == 'text':
            print(workout.export_to_text(Keys.UNITS_METRIC_KEY))
        elif format == 'json':
            print(workout.export_to_json_str(Keys.UNITS_METRIC_KEY))
        elif format == 'ics':
            tempfile_name = generate_temp_file_name(".ics")
            ics_str = workout.export_to_ics(Keys.UNITS_METRIC_KEY)
            with open(tempfile_name, 'wt') as local_file:
                local_file.write(ics_str)
            print("Exported a workout to " + tempfile_name + ".")
        elif format == 'zwo':
            tempfile_name = generate_temp_file_name(".zwo")
            zwo_str = workout.export_to_zwo(tempfile_name)
            with open(tempfile_name, 'wt') as local_file:
                local_file.write(zwo_str)
            print("Exported a workout to " + tempfile_name + ".")

@celery_worker.task(ignore_result=True)
def generate_workout_plan_for_user(user_str, internal_task_id):
    """Entry point for the celery worker."""
    global g_model

    print("Starting workout plan generation...")

    user_obj = json.loads(user_str)
    generator = WorkoutPlanGenerator(Config.Config(), user_obj)
    generator.generate_plan_for_user(g_model)

    print("Workout plan generation finished.")

@celery_worker.task()
def generate_workout_plan_from_inputs(inputs, internal_task_id):
    """Entry point for the celery worker."""
    global g_model

    print("Starting workout plan generation...")

    generator = WorkoutPlanGenerator(Config.Config(), None)
    generator.generate_plan_from_inputs(g_model, inputs)

    print("Workout plan generation finished.")

def main():
    """Entry point for a workout plan generator."""
    global g_model

    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", default="", help="The user ID for whom we are to generate a workout plan.", required=False)
    parser.add_argument("--train", default="", help="The path to the training plan model.", required=False)
    parser.add_argument("--format", default="text", help="The output format.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if len(args.train) > 0:
       g_model = generate_model(args.train, args.format)

    if len(args.user_id) > 0:
        data = {}
        data['user_id'] = args.user_id
        workouts = generate_workout_plan_for_user(json.dumps(data), None)


if __name__ == "__main__":
    main()
