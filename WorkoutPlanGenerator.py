# Copyright 2019 Michael J Simms
"""Handles the generation of a workout plan. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import argparse
import celery
import datetime
import json
import logging
import os
import numpy as np
import pandas
import sys
import tensorflow as tf
import time
import traceback
import uuid
import AnalysisScheduler
import BikePlanGenerator
import DataMgr
import UserMgr
import Keys
import Units
import RunPlanGenerator
import SwimPlanGenerator
import WorkoutScheduler

g_model = None

METERS_PER_HALF_MARATHON = 13.1 * Units.METERS_PER_MILE
METERS_PER_MARATHON = 26.2 * Units.METERS_PER_MILE

class WorkoutPlanGenerator(object):
    """Class for performing the computationally expensive workout plan generation tasks."""

    def __init__(self, user_obj):
        self.user_obj = user_obj
        self.data_mgr = DataMgr.DataMgr(None, "", AnalysisScheduler.AnalysisScheduler(), None, None)
        self.user_mgr = UserMgr.UserMgr(None)
        super(WorkoutPlanGenerator, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        print(log_str)
        logger = logging.getLogger()
        if logger is not None:
            logger.debug(log_str)
    
    @staticmethod
    def calculate_goal_distances(inputs):
        """Adds the goal distances to the inputs."""
        goal = inputs[Keys.GOAL_KEY]
        goal_lower = goal.lower()

        inputs[Keys.GOAL_SWIM_DISTANCE_KEY] = 0.0
        inputs[Keys.GOAL_BIKE_DISTANCE_KEY] = 0.0
        inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 0.0

        if goal_lower == Keys.GOAL_FITNESS_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 5000.0
        elif goal_lower == Keys.GOAL_5K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 5000.0
        elif goal_lower == Keys.GOAL_10K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 10000.0
        elif goal_lower == Keys.GOAL_15K_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = 15000.0
        elif goal_lower == Keys.GOAL_HALF_MARATHON_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = METERS_PER_HALF_MARATHON
        elif goal_lower == Keys.GOAL_MARATHON_RUN_KEY.lower():
            inputs[Keys.GOAL_RUN_DISTANCE_KEY] = METERS_PER_MARATHON

        return inputs

    @staticmethod
    def update_summary_data_cb(context, activity, user_id):
        """Callback function for update_summary_data."""
        if Keys.ACTIVITY_SUMMARY_KEY not in activity:
            context.data_mgr.analyze_activity(activity, user_id)

    def calculate_inputs(self, user_id):
        """Looks through the user's data and calculates the algorithm's inputs."""

        inputs = {}

        now = time.time()
        weeks_until_goal = None # Number of weeks until the goal, or None if not applicable
        longest_run_in_four_weeks = None  # Longest run in the last four weeks
        longest_run_week_1 = None
        longest_run_week_2 = None
        longest_run_week_3 = None

        # Analyze any unanalyzed activities.
        self.data_mgr.analyze_unanalyzed_activities(user_id, DataMgr.FOUR_WEEKS)

        # Fetch the detail of the user's goal.
        goal, goal_date = self.data_mgr.retrieve_user_goal(user_id)
        if goal is None:
            raise Exception("A goal has not been defined.")
        if goal_date is None:
            raise Exception("A goal date has not been defined.")
        if goal is not Keys.GOAL_FITNESS_KEY:

            # Sanity-check the goal date.
            if goal_date <= now:
                raise Exception("The goal date should be in the future.")

            # Convert the goal time into weeks.
            weeks_until_goal = (goal_date - now) / (7 * 24 * 60 * 60)

        # Is the user interested in just completion, or do they care about pace/speed?
        goal_type = self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_TYPE_KEY)

        # This will trigger the callback for each of the user's activities.
        self.data_mgr.retrieve_each_user_activity(self, user_id, WorkoutPlanGenerator.update_summary_data_cb)

        # Look through the user's six month records.
        cycling_bests, running_bests, cycling_summary, running_summary = self.data_mgr.retrieve_recent_bests(user_id, DataMgr.SIX_MONTHS)

        # Estimate running paces from the user's six month records.
        if running_bests is not None:
            running_paces = self.data_mgr.compute_run_training_paces(user_id, running_bests)
        else:
            running_paces = {}

        # Estimate an FTP from the last six months of cycling data.
        if cycling_bests is not None:
            if Keys.THRESHOLD_POWER in cycling_bests:
                threshold_power = cycling_bests[Keys.THRESHOLD_POWER]
                best_recent_threshold_power = self.data_mgr.retrieve_user_estimated_ftp(user_id)
                if best_recent_threshold_power is None or threshold_power > best_recent_threshold_power:
                    self.data_mgr.store_user_estimated_ftp(user_id, threshold_power)

        # Look through the user's four week records.
        cycling_bests, running_bests, cycling_summary, running_summary = self.data_mgr.retrieve_recent_bests(user_id, DataMgr.FOUR_WEEKS)
        if running_bests is not None and Keys.LONGEST_DISTANCE in running_bests:
            longest_run_in_four_weeks = running_bests[Keys.LONGEST_DISTANCE]
            longest_run_in_four_weeks = longest_run_in_four_weeks[0]

        # Get some data from prior weeks data.
        _, running_bests_week_1, _, running_summary_week_1 = self.data_mgr.retrieve_recent_bests(user_id, DataMgr.ONE_WEEK)
        if running_bests_week_1 is not None and Keys.LONGEST_DISTANCE in running_bests_week_1:
            longest_run_week_1 = running_bests_week_1[Keys.LONGEST_DISTANCE]
            longest_run_week_1 = longest_run_week_1[0]
        _, running_bests_week_2, _, running_summary_week_2 = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - (DataMgr.ONE_WEEK * 2), now - (DataMgr.ONE_WEEK * 1))
        if running_bests_week_2 is not None and Keys.LONGEST_DISTANCE in running_bests_week_2:
            longest_run_week_2 = running_bests_week_2[Keys.LONGEST_DISTANCE]
            longest_run_week_2 = longest_run_week_2[0]
        _, running_bests_week_3, _, running_summary_week_3 = self.data_mgr.retrieve_bounded_activity_bests_for_user(user_id, now - (DataMgr.ONE_WEEK * 3), now - (DataMgr.ONE_WEEK * 2))
        if running_bests_week_3 is not None and Keys.LONGEST_DISTANCE in running_bests_week_3:
            longest_run_week_3 = running_bests_week_3[Keys.LONGEST_DISTANCE]
            longest_run_week_3 = longest_run_week_3[0]

        # Compute the user's age in years.
        birthday = int(self.user_mgr.retrieve_user_setting(user_id, Keys.BIRTHDAY_KEY))
        age_years = (now - birthday) / (365.25 * 24 * 60 * 60)

        # Compute average running and cyclist distances.
        avg_cycling_distance = 0.0
        avg_running_distance = 0.0
        if cycling_summary is not None:
            if Keys.TOTAL_ACTIVITIES in cycling_summary and Keys.TOTAL_DISTANCE in cycling_summary:
                if cycling_summary[Keys.TOTAL_ACTIVITIES] > 0:
                    avg_cycling_distance = cycling_summary[Keys.TOTAL_DISTANCE] / cycling_summary[Keys.TOTAL_ACTIVITIES]
        if running_summary is not None:
            if Keys.TOTAL_ACTIVITIES in running_summary and Keys.TOTAL_DISTANCE in running_summary:
                if running_summary[Keys.TOTAL_ACTIVITIES] > 0:
                    avg_running_distance = running_summary[Keys.TOTAL_DISTANCE] / running_summary[Keys.TOTAL_ACTIVITIES]

        # Compute an experience level for the user.
        experience_level = self.user_mgr.retrieve_user_setting(user_id, Keys.EXPERIENCE_LEVEL_KEY)

        # Are we in a taper?
        if weeks_until_goal < 2 and goal_type == Keys.GOAL_MARATHON_RUN_KEY:
            in_taper = 1
        elif weeks_until_goal < 1:
            in_taper = 1
        else:
            in_taper = 0

        # Store all the inputs in a dictionary.
        if len(running_paces) == 0:
            inputs[Keys.SPEED_RUN_PACE] = None
            inputs[Keys.TEMPO_RUN_PACE] = None
            inputs[Keys.LONG_RUN_PACE] = None
            inputs[Keys.EASY_RUN_PACE] = None
        else:
            inputs = running_paces
        inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY] = longest_run_in_four_weeks
        inputs[Keys.LONGEST_RUN_WEEK_1_KEY] = longest_run_week_1
        inputs[Keys.LONGEST_RUN_WEEK_2_KEY] = longest_run_week_2
        inputs[Keys.LONGEST_RUN_WEEK_3_KEY] = longest_run_week_3
        inputs[Keys.AGE_YEARS_KEY] = age_years
        inputs[Keys.EXPERIENCE_LEVEL_KEY] = experience_level
        inputs[Keys.GOAL_KEY] = goal
        inputs[Keys.GOAL_TYPE_KEY] = goal_type
        inputs[Keys.WEEKS_UNTIL_GOAL_KEY] = weeks_until_goal
        inputs[Keys.WORKOUT_AVG_CYCLING_DISTANCE_IN_FOUR_WEEKS] = avg_cycling_distance
        inputs[Keys.WORKOUT_AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS] = avg_running_distance
        inputs[Keys.WORKOUT_IN_TAPER_KEY] = in_taper

        # Adds the goal distances to the inputs.
        inputs = WorkoutPlanGenerator.calculate_goal_distances(inputs)

        print("Inputs: " + str(inputs))
        return inputs

    def generate_workouts(self, user_id, inputs):
        """Generates workouts for the specified user to perform in the next week."""

        workouts = []

        swim_planner = SwimPlanGenerator.SwimPlanGenerator(user_id)
        bike_planner = BikePlanGenerator.BikePlanGenerator(user_id)
        run_planner = RunPlanGenerator.RunPlanGenerator(user_id)

        # Generate the swim workouts.
        if not swim_planner.is_workout_plan_possible(inputs):
            raise Exception("The swim distance goal is not feasible in the time alloted.")
        swim_workouts = swim_planner.gen_workouts_for_next_week(inputs)
        workouts.extend(swim_workouts)

        # Generate the bike workouts.
        if not bike_planner.is_workout_plan_possible(inputs):
            raise Exception("The bike distance goal is not feasible in the time alloted.")
        bike_workouts = bike_planner.gen_workouts_for_next_week(inputs)
        workouts.extend(bike_workouts)

        # Generate the run workouts.
        if not run_planner.is_workout_plan_possible(inputs):
            raise Exception("The run distance goal is not feasible in the time alloted.")
        run_workouts = run_planner.gen_workouts_for_next_week(inputs)
        workouts.extend(run_workouts)

        return workouts

    def generate_workouts_using_model(self, user_id, inputs, model):
        """Runs the neural network specified by 'model' to generate the workout plan."""

        # Convert the input dictionary to an array as required by tf.
        model_inputs = [ ]
        model_inputs.append(inputs[Keys.SPEED_RUN_PACE])
        model_inputs.append(inputs[Keys.TEMPO_RUN_PACE])
        model_inputs.append(inputs[Keys.LONG_RUN_PACE])
        model_inputs.append(inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY])
        model_inputs.append(inputs[Keys.LONGEST_RUN_WEEK_1_KEY])
        model_inputs.append(inputs[Keys.LONGEST_RUN_WEEK_2_KEY])
        model_inputs.append(inputs[Keys.LONGEST_RUN_WEEK_3_KEY])
        model_inputs.append(inputs[Keys.AGE_YEARS_KEY])
        model_inputs.append(inputs[Keys.EXPERIENCE_LEVEL_KEY])
        model_inputs.append(inputs[Keys.GOAL_KEY])
        model_inputs.append(inputs[Keys.GOAL_TYPE_KEY])
        model_inputs.append(inputs[Keys.WEEKS_UNTIL_GOAL_KEY])
        model_inputs.append(inputs[Keys.WORKOUT_AVG_CYCLING_DISTANCE_IN_FOUR_WEEKS])
        model_inputs.append(inputs[Keys.WORKOUT_AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS])

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

    def store_plan(self, user_id, workouts):
        """Saves the user's workouts to the database."""
        for workout_obj in workouts:
            result = self.data_mgr.create_workout(user_id, workout_obj)
            if not result:
                print("Failed to save a workout to the database.")

    def generate_plan(self, model):
        """Entry point for workout plan generation. If a model is not provided then a simpler, non-neural network-based algorithm, is used instead."""

        # Sanity check.
        if self.user_obj is None:
            self.log_error("User information not provided.")
            return []
        if model is None:
            self.log_error("Model not provided. Will use non-ML algorithm instead.")

        workouts = []

        try:
            user_id = self.user_obj[Keys.WORKOUT_PLAN_USER_ID_KEY]
            inputs = self.calculate_inputs(user_id)

            # Generate the workouts.
            if model is None:
                workouts = self.generate_workouts(user_id, inputs)
            else:
                workouts = self.generate_workouts_using_model(user_id, inputs, model)

            # Organize the workouts into a schedule.
            workouts = self.organize_schedule(user_id, workouts)

            # Save to the database.
            self.store_plan(user_id, workouts)
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
    
@celery_worker.task()
def generate_workout_plan(user_str, format):
    """Entry point for the celery worker."""
    global g_model

    print("Starting workout plan generation...")

    user_obj = json.loads(user_str)
    generator = WorkoutPlanGenerator(user_obj)

    # Generate the workouts.
    workouts = generator.generate_plan(g_model)

    # Export the workouts to local files, if requested.
    if format is not None:
        for workout in workouts:
            if format == 'text':
                print(workout.export_to_text())
            elif format == 'json':
                print(workout.export_to_json_str())
            elif format == 'ics':
                tempfile_name = generate_temp_file_name(".ics")
                ics_str = workout.export_to_ics()
                with open(tempfile_name, 'wt') as local_file:
                    local_file.write(ics_str)
                print("Exported a workout to " + tempfile_name + ".")
            elif format == 'zwo':
                tempfile_name = generate_temp_file_name(".zwo")
                zwo_str = workout.export_to_zwo(tempfile_name)
                with open(tempfile_name, 'wt') as local_file:
                    local_file.write(zwo_str)
                print("Exported a workout to " + tempfile_name + ".")

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
        generate_workout_plan(json.dumps(data), args.format)


if __name__ == "__main__":
    main()
