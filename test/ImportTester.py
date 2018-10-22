# Copyright 2017 Michael J Simms
"""Unit tests for file imports."""

import argparse
import inspect
import logging
import os
import sys
import uuid

# Locate and load the importer module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Importer
import LocationAnalyzer
import SensorAnalyzerFactory
import StraenKeys
import Summarizer

ERROR_LOG = 'error.log'


class TestActivityWriter(Importer.ActivityWriter):
    """Subclass that implements the location writer and will receive the locations as they are read from the file."""

    def __init__(self):
        Importer.ActivityWriter.__init__(self)
        self.summarizer = Summarizer.Summarizer()
        self.current_activity_id = None
        self.location_analyzer = None
        self.sensor_analyzers = []

    def create_activity(self, username, stream_name, stream_description, activity_type):
        """Inherited from ActivityWriter. Called when we start reading an activity file."""
        self.location_analyzer = LocationAnalyzer.LocationAnalyzer() # Need a fresh analyzer object for each activity
        self.current_activity_id = str(uuid.uuid4())
        title_str = "Activity Type: " + activity_type
        print(title_str)
        print("-" * len(title_str))
        return None, None

    def create_track(self, device_str, activity_id, track_name, track_description):
        """Inherited from ActivityWriter."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Inherited from ActivityWriter. Called for each location that is read from the input file."""
        self.location_analyzer.append_location(date_time, latitude, longitude, altitude)

    def create_sensor_reading(self, device_str, activity_id, date_time, key, value):
        """Inherited from ActivityWriter. Called for each sensor reading that is read from the input file."""
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
        """Inherited from ActivityWriter. Called for post-processing."""
        for sensor_analyzer in self.sensor_analyzers:
            title_str = sensor_analyzer.type + ":"
            print(title_str)
            print("-" * len(title_str))
            print(sensor_analyzer.analyze())
        print("Location-Based Calculations:")
        print("----------------------------")
        print("Total Distance: {:.2f} meters".format(self.location_analyzer.total_distance))
        print("Vertical Ascent: {:.2f} meters".format(self.location_analyzer.total_vertical))
        if self.location_analyzer.start_time is not None and self.location_analyzer.last_time is not None:
            total_time = (self.location_analyzer.last_time - self.location_analyzer.start_time) / 1000
            print("Total Time: {:.2f} seconds".format(total_time))
        if self.location_analyzer.avg_speed is not None:
            print("Average Speed: {:.2f} meters/second".format(self.location_analyzer.avg_speed))
        if self.location_analyzer.current_speed is not None:
            print("Current Speed: {:.2f} meters/second".format(self.location_analyzer.current_speed))
        if self.location_analyzer.best_speed is not None:
            print("Best Speed: {:.2f}".format(self.location_analyzer.best_speed))

        best = self.location_analyzer.get_best_time(StraenKeys.BEST_1K)
        if best is not None:
            print("Best KM: {:.2f} seconds".format(best))
        best = self.location_analyzer.get_best_time(StraenKeys.BEST_MILE)
        if best is not None:
            print("Best Mile: {:.2f} seconds".format(best))
        best = self.location_analyzer.get_best_time(StraenKeys.BEST_5K)
        if best is not None:
            print("Best 5K: {:.2f} seconds".format(best))
        best = self.location_analyzer.get_best_time(StraenKeys.BEST_10K)
        if best is not None:
            print("Best 10K: {:.2f} seconds".format(best))
        best = self.location_analyzer.get_best_time(StraenKeys.BEST_HALF_MARATHON)
        if best is not None:
            print("Best Half Marathon: {:.2f} seconds".format(best))

        self.summarizer.add_activity_data(self.current_activity_id, self.location_analyzer.bests)
        self.current_activity_id = None
        self.location_analyzer = None
        self.sensor_analyzers = []

def main():
    """Starts the tests."""

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

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
        title_str = "Processing all files in " + test_dir + ":"
        print(title_str + "\n")
        for current_file in files:
            full_path = os.path.join(subdir, current_file)
            title_str = "Processing: " + full_path
            print("=" * len(title_str))
            print(title_str)
            print("=" * len(title_str))
            _, temp_file_ext = os.path.splitext(full_path)
            if importer.import_file("test user", full_path, temp_file_ext):
                print("Success!\n")
                successes.append(current_file)
            else:
                print("Failure!\n")
                failures.append(current_file)

    # Print the summary data.
    title_str = "Bests:"
    print(title_str)
    print("=" * len(title_str))
    for key in store.summarizer.bests:
        print(key + " = " + str(store.summarizer.bests[key]))
    print("\n")

    # Print the success and failure summary.
    title_str = "Summary:"
    print(title_str)
    print("=" * len(title_str))
    print("Num success: " + str(len(successes)))
    print("Num failures: " + str(len(failures)))
    for failure in failures:
        print("- " + failure)

if __name__ == "__main__":
    main()
