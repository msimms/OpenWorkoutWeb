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
import datetime
import inspect
import json
import logging
import os
import sys

# Locate and load the importer module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Keys
import WorkoutPlanGenerator
import WorkoutScheduler

ERROR_LOG = 'error.log'

def run_unit_tests(input_file_name):
    """Entry point for the unit tests."""

    successes = []
    failures = []

    # Load the test data.
    with open(input_file_name, 'r') as f:
        test_json = json.load(f)
        test_inputs = test_json["inputs"]

        generator = WorkoutPlanGenerator.WorkoutPlanGenerator(None)
        scheduler = WorkoutScheduler.WorkoutScheduler(None)

        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).date()
        start_time = today + datetime.timedelta(days=7-today.weekday())

        # Generate a plan for each test input.
        for test_input in test_inputs:

            # Run the inputs through the workout generator.
            print("-" * 40)
            print("Input: ")
            print("-" * 40)
            print(test_input)
            print("-" * 40)
            print("Generating workouts...")
            print("-" * 40)
            workouts = generator.generate_plan_from_inputs(None, test_input)
            print("-" * 40)
            print("Exporting workouts...")
            print("-" * 40)
            WorkoutPlanGenerator.export_workouts(workouts, 'text')
            print("-" * 40)
            print("Scheduling workouts...")
            print("-" * 40)
            schedule = scheduler.schedule_workouts(workouts, start_time)
            for workout in schedule:
                print(workout.export_to_text(Keys.UNITS_METRIC_KEY))

    return len(failures) == 0

def main():
    """Starts the tests."""

    # Setup the logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Parse the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="File to process", required=True)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    # Do the tests.
    try:
        run_unit_tests(args.file)
    except Exception as e:
        print("Test aborted!\n")
        print(e)

if __name__ == "__main__":
    main()
