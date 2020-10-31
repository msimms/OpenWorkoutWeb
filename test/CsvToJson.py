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
"""CSV converter, part of the test harness for workout plan generation."""

import argparse
import csv
import json

def is_float(test_str):
    """Returns True if the string appears to be a valid float."""
    try:
        float(test_str)
        return True
    except ValueError:
        pass
    return False

def make_json(csv_file_name, json_file_name):
    data = {}
    inputs = []

    # Open a csv reader called DictReader
    with open(csv_file_name) as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            for key in row:
                if is_float(row[key]):
                    row[key] = float(row[key])
            inputs.append(row)

    data["inputs"] = inputs
    with open(json_file_name, 'wt') as json_file:
        json_file.write(json.dumps(data, indent=3))

def main():
    # Parse the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, action="store", default="", help="CSV Input File", required=True)
    parser.add_argument("--json", type=str, action="store", default="", help="JSON Output File", required=True)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    make_json(args.csv, args.json)

if __name__ == "__main__":
    main()
