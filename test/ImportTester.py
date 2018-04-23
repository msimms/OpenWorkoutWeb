# Copyright 2017 Michael J Simms
"""Unit tests for file imports."""

import argparse
import inspect
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Importer

class TestLocationWriter(Importer.LocationWriter):
    """Subclass that implements the location writer and will receive the locations as they are read from the file."""

    def create(self, username, stream_name, stream_description, activity_type):
        return None, None

    def create_track(self, device_str, activity_id, track_name, track_description):
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        print device_str, activity_id, date_time, latitude, longitude, altitude

    def create_sensor_reading(self, device_str, activity_id, date_time, key, value):
        print device_str, activity_id, date_time, key, value

def main():
    """Starts the tests."""

    successes = []
    failures = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="Directory of files to be processed", required=True)
    args = parser.parse_args()

    store = TestLocationWriter()
    importer = Importer.Importer(store)
    test_dir = os.path.abspath(os.path.join('.', args.dir))

    for subdir, _, files in os.walk(test_dir):
        print "Processing all files in: " + test_dir
        for current_file in files:
            full_path = os.path.join(subdir, current_file)
            print "Processing: " + full_path
            _, temp_file_ext = os.path.splitext(full_path)
            if importer.import_file("test user", full_path, temp_file_ext):
                print "Success"
                successes.append(current_file)
            else:
                print "Failed"
                failures.append(current_file)

    print "Num success: " + str(len(successes))
    print "Num failures: " + str(len(failures))

if __name__ == "__main__":
    main()
