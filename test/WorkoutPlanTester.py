# Copyright 2020 Michael J Simms
"""Unit tests for workout plan generation."""

import argparse
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

ERROR_LOG = 'error.log'

def run_unit_tests(input_file_name):
    """Entry point for the unit tests."""

    successes = []
    failures = []

    gen = WorkoutPlanGenerator.WorkoutPlanGenerator(None)

    # Load the test data.
    with open(input_file_name, 'r') as f:
        test_json = json.load(f)
        test_inputs = test_json["inputs"]

        # Generate a plan for each test input.
        for test_input in test_inputs:
            print("Input: " + str(test_input))
            print("Output:")
            workouts = gen.generate_workouts(0, test_input)
            for workout in workouts:
                print(workout.export_to_text())

    return len(failures) == 0

def main():
    """Starts the tests."""

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Parse the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="File to process", required=True)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    run_unit_tests(args.file)

if __name__ == "__main__":
    main()
