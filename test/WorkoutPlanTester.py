#! /usr/bin/env python
# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Mike Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Unit tests for workout plan generation."""

import argparse
import csv
import datetime
import inspect
import logging
import os
import sys
import time

# Locate and load modules from the main source directory.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Config
import Keys
import WorkoutPlanGenerator
import WorkoutScheduler

ERROR_LOG = 'error.log'

def run_unit_test_from_file(config, input_file_name):
    """Entry point for the unit tests that come from running input sets from a csv file"""
    """through the workout plan generation algorithm."""

    # Load the test data.
    with open(input_file_name, 'r') as f:
        csv_data = csv.reader(f)

        generator = WorkoutPlanGenerator.WorkoutPlanGenerator(config, None)
        scheduler = WorkoutScheduler.WorkoutScheduler(None)

        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).date()
        start_time = today + datetime.timedelta(days=7-today.weekday())
        column_names = {}

        # Generate a plan for each test input.
        for test_input in csv_data:

            # The first row has the key names.
            if not column_names:
                column_names = test_input

            # Subsequent rows are test data.
            else:

                # Cleanup the inputs, convert strings to numbers where applicable.
                sanitized_inputs = []
                for item in test_input:
                    try:
                        sanitized_inputs.append(float(item))
                    except:
                        sanitized_inputs.append(item)

                inputs = dict(zip(column_names, sanitized_inputs))
                print(inputs)

                # Run the inputs through the workout generator.
                print("-" * 40)
                print("Input: ")
                print("-" * 40)
                print(inputs)
                print("-" * 40)
                print("Generating workouts...")
                print("-" * 40)
                workouts = generator.generate_plan_from_inputs(None, inputs)
                print("-" * 40)
                print("Exporting workouts...")
                print("-" * 40)
                WorkoutPlanGenerator.export_workouts(workouts, 'text')
                print("-" * 40)
                print("Scheduling workouts...")
                print("-" * 40)

                # Run the workouts through the scheduler.
                schedule = scheduler.schedule_workouts(workouts, start_time)
                for workout in schedule:
                    print(workout.export_to_text(Keys.UNITS_METRIC_KEY))

    return column_names

def run_algorithmic_unit_tests(config, input_names, age_years, experience_level, comfort_level, goal, weeks_until_goal, goal_type):
    """Start with an athlete for which we have no data and generate a workout plan."""
    """Use the workouts for one week to generate the plan for the next week (as if"""
    """the user executed the plan perfectly."""
    generator = WorkoutPlanGenerator.WorkoutPlanGenerator(config, None)
    scheduler = WorkoutScheduler.WorkoutScheduler(None)

    now = time.time()
    longest_runs_by_week = [0.0] * 4 # Longest run for each of the recent four weeks
    longest_rides_by_week = [0.0] * 4 # Longest bike rides for each of the recent four weeks
    run_intensity_by_week = [0.0] * 4 # Total training intensity for each of the recent four weeks
    cycling_intensity_by_week = [0.0] * 4 # Total training intensity for each of the recent four weeks
    running_paces = {}

    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).date()
    start_time = today + datetime.timedelta(days=7-today.weekday())

    input_values = [0.0] * len(input_names)
    inputs = dict(zip(input_names, input_values))

    week_num = 1
    done = False

    while not done:

        print("-" * 40)
        print("Week " + str(week_num))
        print("-" * 40)

        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY] = longest_runs_by_week[0]
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY] = longest_runs_by_week[1]
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY] = longest_runs_by_week[2]
        inputs[Keys.PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY] = longest_runs_by_week[3]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_1_KEY] = longest_rides_by_week[0]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_2_KEY] = longest_rides_by_week[1]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_3_KEY] = longest_rides_by_week[2]
        inputs[Keys.PLAN_INPUT_LONGEST_RIDE_WEEK_4_KEY] = longest_rides_by_week[3]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_1_KEY] = run_intensity_by_week[0] + cycling_intensity_by_week[0]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_2_KEY] = run_intensity_by_week[1] + cycling_intensity_by_week[1]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_3_KEY] = run_intensity_by_week[2] + cycling_intensity_by_week[2]
        inputs[Keys.PLAN_INPUT_TOTAL_INTENSITY_WEEK_4_KEY] = run_intensity_by_week[3] + cycling_intensity_by_week[3]
        inputs[Keys.PLAN_INPUT_AGE_YEARS_KEY] = age_years
        inputs[Keys.PLAN_INPUT_EXPERIENCE_LEVEL_KEY] = experience_level
        inputs[Keys.PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY] = comfort_level
        inputs[Keys.PLAN_INPUT_GOAL_KEY] = goal
        inputs[Keys.GOAL_TYPE_KEY] = goal_type
        inputs[Keys.PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY] = weeks_until_goal

        print("Input:")
        print(inputs)
        workouts = generator.generate_plan_from_inputs(None, inputs)

        # Run the workouts through the scheduler.
        print("Output:")
        schedule = scheduler.schedule_workouts(workouts, start_time)
        for workout in schedule:
            print(workout.export_to_text(Keys.UNITS_METRIC_KEY))

        # Compute next week's inputs.
        longest_runs_by_week[3] = longest_runs_by_week[2]
        longest_runs_by_week[2] = longest_runs_by_week[1]
        longest_runs_by_week[1] = longest_runs_by_week[0]
        longest_runs_by_week[0] = []
        longest_rides_by_week[3] = longest_rides_by_week[2]
        longest_rides_by_week[2] = longest_rides_by_week[1]
        longest_rides_by_week[1] = longest_rides_by_week[0]
        longest_rides_by_week[0] = []
        run_intensity_by_week[3] = run_intensity_by_week[2]
        run_intensity_by_week[2] = run_intensity_by_week[1]
        run_intensity_by_week[1] = run_intensity_by_week[0]
        run_intensity_by_week[0] = []
        cycling_intensity_by_week[3] = cycling_intensity_by_week[2]
        cycling_intensity_by_week[2] = cycling_intensity_by_week[1]
        cycling_intensity_by_week[1] = cycling_intensity_by_week[0]
        cycling_intensity_by_week[0] = []
        for workout in workouts:
            workout_distance = workout.total_workout_distance_meters()
            if workout.sport_type in Keys.RUNNING_ACTIVITIES:
                if longest_runs_by_week or workout_distance > max(longest_runs_by_week[0]):
                    longest_runs_by_week[0] = workout_distance
            if workout.sport_type in Keys.CYCLING_ACTIVITIES:
                if longest_rides_by_week or workout_distance > max(longest_rides_by_week[0]):
                    longest_rides_by_week[0] = workout_distance

        week_num = week_num + 1
        weeks_until_goal = weeks_until_goal - 1
        done = weeks_until_goal == 0

def main():
    """Starts the tests."""

    # Setup the logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Parse the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="", help="The configuration file.", type=str, action="store", required=True)
    parser.add_argument("--file", help="CSV test file to process", type=str, action="store", required=True)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    # Load the config file.
    config = Config.Config()
    if len(args.config) > 0:
        config.load(args.config)

    # Do the tests.
    try:
        print("Tests using the CSV file.")
        print("-" * 40)
        column_names = run_unit_test_from_file(config, args.file)
        print("-" * 40)
        print("Tests using algorithmic inputs.")
        print("-" * 40)
        goal = Keys.GOAL_5K_RUN_KEY
        weeks_until_goal = 3
        run_algorithmic_unit_tests(config, column_names, 40.0, 5, 5, goal, weeks_until_goal, Keys.GOAL_TYPE_COMPLETION)
    except Exception as e:
        print("Test aborted!\n")
        print(e)

if __name__ == "__main__":
    main()
