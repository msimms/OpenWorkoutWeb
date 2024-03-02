#! /usr/bin/env python
# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Michael J Simms
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
"""Unit tests."""

import argparse
import inspect
import os
import sys
import traceback

import ApiTester
import CsvToJson
import ImportTester
import WorkoutPlanTester

# Locate and load the config module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Config

ERROR_LOG = 'error.log'

def do_api_tests(url, username, password, realname):
    ApiTester.run_unit_tests(url, username, password, realname)

def do_importer_tests(test_files_dir_name):
    ImportTester.run_unit_tests(test_files_dir_name)

def do_workout_plan_tests(config):
    testdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    csv_file_name = os.path.join(testdir, "WorkoutTrainingInputs.csv")
    json_file_name = os.path.join(testdir, "input.json")
    CsvToJson.make_json(csv_file_name, json_file_name)
    WorkoutPlanTester.run_unit_tests(config, json_file_name)

def main():
    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="", help="The configuration file.", type=str, action="store", required=True)
    parser.add_argument("--url", default="https://127.0.0.1:8080", help="The root address of the website", required=True)
    parser.add_argument("--username", default="foo@example.com", help="The username to use for the test", required=False)
    parser.add_argument("--password", default="foobar123", help="The password to use for the test", required=False)
    parser.add_argument("--realname", default="Mr Foo", help="The user's real name", required=False)
    parser.add_argument("--importdir", default=os.path.dirname(os.path.realpath(__file__)), help="Directory of files to to import", required=True, type=str, action="store",)

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
        print("API Tests:")
        do_api_tests(args.url, args.username, args.password, args.realname)
        print("Importer Tests:")
        do_importer_tests(args.importdir)
        print("Workout Plan Tests:")
        do_workout_plan_tests(config)
    except AssertionError as e:
        print("Test aborted due to an assertion failure!\n")
        print(traceback.format_exc())
        print(e)
    except Exception as e:
        print("Test aborted!\n")
        print(traceback.format_exc())
        print(e)

if __name__ == "__main__":
    main()
