# Copyright 2017 Michael J Simms
"""Unit tests for file imports."""

import argparse
import inspect
import os
import sys

# Locate and load the importer module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Importer
import TrackAnalyzer
import SensorAnalyzerFactory

class TestActivityWriter(Importer.ActivityWriter):
    """Subclass that implements the location writer and will receive the locations as they are read from the file."""

    def __init__(self):
        Importer.ActivityWriter.__init__(self)
        self.track_analyzer = None
        self.sensor_analyzers = []

    def create_activity(self, username, stream_name, stream_description, activity_type):
        self.track_analyzer = TrackAnalyzer.TrackAnalyzer() # Need a fresh analyzer object for each activity
        print "Activity Type: " + activity_type
        return None, None

    def create_track(self, device_str, activity_id, track_name, track_description):
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Called for each location that is read from the input file."""
        self.track_analyzer.append_location(date_time, latitude, longitude, altitude)

    def create_sensor_reading(self, device_str, activity_id, date_time, key, value):
        """Called for each sensor reading that is read from the input file."""
        found = False
        for sensor_analyzer in self.sensor_analyzers:
            if sensor_analyzer.type == key:
                sensor_analyzer.append_sensor_value(date_time, value)
                found = True
                break
        if not found:
            factory = SensorAnalyzerFactory.SensorAnalyzerFactory()
            sensor_analyzer = factory.create(key)
            if sensor_analyzer:
                sensor_analyzer.append_sensor_value(date_time, value)
                self.sensor_analyzers.append(sensor_analyzer)

    def finish_activity(self):
        """Called for post-processing."""
        for sensor_analyzer in self.sensor_analyzers:
            sensor_analyzer.analyze()
        self.track_analyzer = None
        self.sensor_analyzers = []

def main():
    """Starts the tests."""

    successes = []
    failures = []

    # Parse the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="Directory of files to be processed", required=True)
    args = parser.parse_args()

    store = TestActivityWriter()
    importer = Importer.Importer(store)
    test_dir = os.path.abspath(os.path.join('.', args.dir))

    # Process each file in the specified directory as well as its subdirectories.
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
