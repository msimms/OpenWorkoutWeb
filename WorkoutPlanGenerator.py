# Copyright 2019 Michael J Simms
"""Handles the generation of a workout plan. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import argparse
import celery
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
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr("", root_dir, AnalysisScheduler.AnalysisScheduler(), None, None)
        self.user_mgr = UserMgr.UserMgr(None, root_dir)
        super(WorkoutPlanGenerator, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        print(log_str)
        logger = logging.getLogger()
        if logger is not None:
            logger.debug(log_str)
    
    @staticmethod
    def goal_enum_to_distances(goal):
        """Converts the goal key/enum value to the equivalent value in meters, returned as an array of [swim, bike, run] distances."""
        if goal == Keys.GOAL_5K_RUN_KEY:
            return [0, 0, 5000]
        elif goal == Keys.GOAL_10K_RUN_KEY:
            return [0, 0, 10000]
        elif goal == Keys.GOAL_15K_RUN_KEY:
            return [0, 0, 15000]
        elif goal == Keys.GOAL_HALF_MARATHON_RUN_KEY:
            return [0, 0, METERS_PER_HALF_MARATHON]
        elif goal == Keys.GOAL_MARATHON_RUN_KEY:
            return [0, 0, METERS_PER_MARATHON]
        return [0, 0, 0]

    @staticmethod
    def goal_enum_to_bike_distance(goal):
        """Converts the goal key/enum value to the equivalent value in meters."""
        return 0

    @staticmethod
    def update_summary_data_cb(context, activity, user_id):
        """Callback function for update_summary_data."""
        if Keys.ACTIVITY_SUMMARY_KEY not in activity:
            analysis_obj = context.data_mgr.analyze(activity, user_id)

    def calculate_inputs(self, user_id):
        """Looks through the user's data and calculates the neural net inputs."""

        inputs = {}

        now = time.time()
        longest_run_in_four_weeks = None  # Longest run in the last four weeks

        # Analyze any unanalyzed activities.
        self.data_mgr.analyze_unanalyzed_activities(user_id, DataMgr.FOUR_WEEKS)

        # Fetch the detail of the user's goal.
        goal = self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_KEY)
        goal_date = int(self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_DATE_KEY))
        if goal_date <= now:
            raise Exception("The goal date should be in the future.")
        weeks_until_goal = (goal_date - now) / (7 * 24 * 60 * 60) # Convert to weeks

        self.data_mgr.retrieve_each_user_activity(self, user_id, WorkoutPlanGenerator.update_summary_data_cb)

        # Look through the user's six month records.
        cycling_bests, running_bests = self.data_mgr.retrieve_recent_bests(user_id, DataMgr.SIX_MONTHS)
        if running_bests is not None:
            running_paces = self.data_mgr.compute_run_training_paces(user_id, running_bests)
        else:
            running_paces = {}
        if cycling_bests is not None:
            if Keys.THRESHOLD_POWER in cycling_bests:
                threshold_power = cycling_bests[Keys.THRESHOLD_POWER]
                best_recent_threshold_power = self.data_mgr.retrieve_user_estimated_ftp(user_id)
                if best_recent_threshold_power is None or threshold_power > best_recent_threshold_power:
                    self.data_mgr.store_user_estimated_ftp(user_id, threshold_power)

        # Look through the user's four week records.
        cycling_bests, running_bests = self.data_mgr.retrieve_recent_bests(user_id, DataMgr.FOUR_WEEKS)
        if running_bests is not None:
            if Keys.LONGEST_DISTANCE in running_bests:
                longest_run_in_four_weeks = running_bests[Keys.LONGEST_DISTANCE]
                longest_run_in_four_weeks = longest_run_in_four_weeks[0]

        # Compute the user's age in years.
        birthday = int(self.user_mgr.retrieve_user_setting(user_id, Keys.BIRTHDAY_KEY))
        age_years = (now - birthday) / (365.25 * 24 * 60 * 60)

        # Compute an experience level for the user.
        experience_level = 0

        # Store all the inputs in a dictionary.
        if len(running_paces) == 0:
            inputs[Keys.SPEED_RUN_PACE] = None
            inputs[Keys.TEMPO_RUN_PACE] = None
            inputs[Keys.LONG_RUN_PACE] = None
            inputs[Keys.EASY_RUN_PACE] = None
        else:
            inputs = running_paces
        inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY] = longest_run_in_four_weeks
        inputs[Keys.AGE_YEARS_KEY] = age_years
        inputs[Keys.EXPERIENCE_LEVEL_KEY] = experience_level
        inputs[Keys.GOAL_KEY] = goal
        inputs[Keys.WEEKS_UNTIL_GOAL_KEY] = weeks_until_goal

        print("Inputs: " + str(inputs))
        return inputs

    def generate_workouts(self, user_id, inputs):
        """Generates workouts for the specified user to perform in the next week."""
        swim_planner = SwimPlanGenerator.SwimPlanGenerator(user_id)
        bike_planner = BikePlanGenerator.BikePlanGenerator(user_id)
        run_planner = RunPlanGenerator.RunPlanGenerator(user_id)

        speed_run_pace = inputs[Keys.SPEED_RUN_PACE]
        tempo_run_pace = inputs[Keys.TEMPO_RUN_PACE]
        long_run_pace = inputs[Keys.LONG_RUN_PACE]
        longest_run_in_four_weeks = inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY]
        goal_distances = WorkoutPlanGenerator.goal_enum_to_distances(inputs[Keys.GOAL_KEY])

        workouts = []

        # Generate the swim workotus.
        if not swim_planner.is_workout_plan_possible(goal_distances[0], inputs):
            raise Exception("The swim distance goal is not feasible in the time alloted.")
        swim_workouts = swim_planner.gen_workouts_for_next_week(goal_distances[0], inputs)
        workouts.extend(swim_workouts)

        # Generate the bike workotus.
        if not bike_planner.is_workout_plan_possible(goal_distances[1], inputs):
            raise Exception("The bike distance goal is not feasible in the time alloted.")
        bike_workouts = bike_planner.gen_workouts_for_next_week(goal_distances[1], inputs)
        workouts.extend(bike_workouts)

        # Generate the run workotus.
        if not run_planner.is_workout_plan_possible(goal_distances[2], inputs):
            raise Exception("The run distance goal is not feasible in the time alloted.")
        run_workouts = run_planner.gen_workouts_for_next_week(goal_distances[2], inputs)
        workouts.extend(run_workouts)

        return workouts

    def generate_workouts_using_model(self, user_id, inputs, model):
        """Runs the neural network specified by 'model' to generate the workout plan."""

        # Convert the input dictionary to an array as required by tf.
        model_inputs = [ inputs[Keys.SPEED_RUN_PACE], inputs[Keys.TEMPO_RUN_PACE], inputs[Keys.LONG_RUN_PACE], inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY], inputs[Keys.AGE_YEARS_KEY], inputs[Keys.EXPERIENCE_LEVEL], inputs[Keys.GOAL], inputs[Keys.WEEKS_UNTIL_GOAL_KEY] ]
        return []

    def organize_schedule(self, user_id, workouts):
        """Arranges the user's workouts into days/weeks, etc. To be called after the outputs are generated, but need cleaning up."""
        scheduler = WorkoutScheduler.WorkoutScheduler(user_id)
        return scheduler.schedule_workouts(workouts)

    def generate_plan(self, model):
        """Entry point for workout plan generation. If a model is not provided then a simpler, non-neural network-based algorithm, is used instead."""

        # Sanity check.
        if self.user_obj is None:
            self.log_error("User information not provided.")
            return []
        if model is None:
            self.log_error("Model not provided. Will use non-ML algorithm instead.")

        outputs = []

        try:
            user_id = self.user_obj[Keys.WORKOUT_PLAN_USER_ID]
            inputs = self.calculate_inputs(user_id)

            # Generate the workouts.
            if model is None:
                outputs = self.generate_workouts(user_id, inputs)
            else:
                outputs = self.generate_workouts_using_model(user_id, inputs, model)

            # Organize the workouts into a schedule.
            outputs = self.organize_schedule(user_id, outputs)
        except:
            self.log_error("Exception when generating a workout plan.")
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
        return outputs

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
def generate_workout_plan(user_str):
    """Entry point for the celery worker."""
    global g_model

    print("Starting workout plan generation...")
    user_obj = json.loads(user_str)
    generator = WorkoutPlanGenerator(user_obj)
    workouts = generator.generate_plan(g_model)
    for workout in workouts:
        tempfile_name = generate_temp_file_name(".zwo")
        workout.export_to_zwo(tempfile_name)
        print("Exported a workout to " + tempfile_name + ".")
    print("Workout plan generation finished.")

def main():
    """Entry point for a workout plan generator."""
    global g_model

    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", default="", help="The user ID for whom we are to generate a workout plan.", required=False)
    parser.add_argument("--train", default="", help="The path to the training plan model.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if len(args.train) > 0:
       g_model = generate_model(args.train)        

    if len(args.user_id) > 0:
        data = {}
        data['user_id'] = args.user_id
        generate_workout_plan(json.dumps(data))


if __name__ == "__main__":
    main()
