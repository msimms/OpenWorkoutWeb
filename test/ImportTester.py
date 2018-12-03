# Copyright 2017 Michael J Simms
"""Unit tests for file imports."""

import argparse
import inspect
import logging
import os
import sys
import time
import uuid

# Locate and load the importer module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import Importer
import LocationAnalyzer
import Keys
import SensorAnalyzerFactory
import Summarizer
import Units

ERROR_LOG = 'error.log'


class TestActivityWriter(Importer.ActivityWriter):
    """Subclass that implements the location writer and will receive the locations as they are read from the file."""

    def __init__(self):
        Importer.ActivityWriter.__init__(self)
        self.summarizer = Summarizer.Summarizer()
        self.current_activity_id = None
        self.current_activity_type = None
        self.current_activity_start_time = None
        self.location_analyzer = None
        self.sensor_analyzers = []

    def create_activity(self, username, user_id, stream_name, stream_description, activity_type, start_time):
        """Inherited from ActivityWriter. Called when we start reading an activity file."""

        self.location_analyzer = LocationAnalyzer.LocationAnalyzer(activity_type) # Need a fresh analyzer object for each activity
        self.current_activity_id = str(uuid.uuid4())
        self.current_activity_type = activity_type
        self.current_activity_start_time = start_time

        title_str = "Activity Type: " + activity_type
        print(title_str)
        print("-" * len(title_str))

        title_str = "ID: " + self.current_activity_id
        print(title_str)
        print("-" * len(title_str))

        return None, None

    def create_track(self, device_str, activity_id, track_name, track_description):
        """Inherited from ActivityWriter."""
        pass

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Inherited from ActivityWriter. Called for each location that is read from the input file."""
        self.location_analyzer.append_location(date_time, latitude, longitude, altitude)
        self.location_analyzer.update_speeds()

    def create_locations(self, device_str, activity_id, locations):
        """Inherited from ActivityWriter. Adds several locations to the database. 'locations' is an array of arrays in the form [time, lat, lon, alt]."""
        for location in locations:
            self.create_location(device_str, activity_id, location[0], location[1], location[2], location[3])

    def create_sensor_reading(self, activity_id, date_time, sensor_type, value):
        """Inherited from ActivityWriter. Called for each sensor reading that is read from the input file."""
        found = False
        for sensor_analyzer in self.sensor_analyzers:
            if sensor_analyzer.type == sensor_type:
                sensor_analyzer.append_sensor_value(date_time, value)
                found = True
                break
        if not found:
            sensor_analyzer = SensorAnalyzerFactory.create(sensor_type)
            if sensor_analyzer:
                sensor_analyzer.append_sensor_value(date_time, value)
                self.sensor_analyzers.append(sensor_analyzer)

    def create_sensor_readings(self, activity_id, sensor_type, values):
        """Inherited from ActivityWriter. Adds several sensor readings to the database. 'values' is an array of arrays in the form [time, value]."""
        for value in values:
            self.create_sensor_reading(activity_id, value[0], sensor_type, value[1]) 

    def finish_activity(self):
        """Inherited from ActivityWriter. Called for post-processing."""

        # Do location-based analysis.
        self.location_analyzer.analyze()

        # Do sensor analysis.
        for sensor_analyzer in self.sensor_analyzers:
            title_str = sensor_analyzer.type + ":"
            print(title_str)
            print("-" * len(title_str))
            sensor_analysis = sensor_analyzer.analyze()
            print(sensor_analysis)
            self.summarizer.add_activity_data(self.current_activity_id, self.current_activity_type, self.current_activity_start_time, sensor_analysis)

        print("Location-Based Calculations:")
        print("----------------------------")

        print("Total Distance: {:.2f} meters".format(self.location_analyzer.total_distance))
        print("Vertical Ascent: {:.2f} meters".format(self.location_analyzer.total_vertical))

        if self.location_analyzer.start_time is not None and self.location_analyzer.last_time is not None:
            total_time = (self.location_analyzer.last_time - self.location_analyzer.start_time) / 1000
            print("Total Time: {:.2f} seconds".format(total_time))
        if self.location_analyzer.avg_speed is not None:
            print("Average Speed: {:.2f} meters/second".format(self.location_analyzer.avg_speed))
            pace = Units.meters_per_sec_to_minutes_per_mile(self.location_analyzer.avg_speed)
            print("Average Pace: {:.2f} minutes/mile".format(pace))
        if self.location_analyzer.current_speed is not None:
            print("Current Speed: {:.2f} meters/second".format(self.location_analyzer.current_speed))
            pace = Units.meters_per_sec_to_minutes_per_mile(self.location_analyzer.current_speed)
            print("Current Pace: {:.2f} minutes/mile".format(pace))
        best = self.location_analyzer.get_best_time(Keys.BEST_SPEED)
        if best is not None:
            print("Best Speed: {:.2f} meters/second".format(best))
            pace = Units.meters_per_sec_to_minutes_per_mile(best)
            print("Best Pace: {:.2f} minutes/mile".format(pace))

        best = self.location_analyzer.get_best_time(Keys.BEST_1K)
        if best is not None:
            print("Best KM: {:.2f} minutes".format(best / 60))
        best = self.location_analyzer.get_best_time(Keys.BEST_MILE)
        if best is not None:
            print("Best Mile: {:.2f} minutes".format(best / 60))
        best = self.location_analyzer.get_best_time(Keys.BEST_5K)
        if best is not None:
            print("Best 5K: {:.2f} minutes".format(best / 60))
        best = self.location_analyzer.get_best_time(Keys.BEST_10K)
        if best is not None:
            print("Best 10K: {:.2f} minutes".format(best / 60))
        best = self.location_analyzer.get_best_time(Keys.BEST_15K)
        if best is not None:
            print("Best 15K: {:.2f} minutes".format(best / 60))
        best = self.location_analyzer.get_best_time(Keys.BEST_HALF_MARATHON)
        if best is not None:
            print("Best Half Marathon: {:.2f} minutes".format(best / 60))
        best = self.location_analyzer.get_best_time(Keys.BEST_MARATHON)
        if best is not None:
            print("Best Marathon: {:.2f} minutes".format(best / 60))

        self.summarizer.add_activity_datum(self.current_activity_id, self.current_activity_type, self.current_activity_start_time, Keys.APP_DISTANCE_KEY, self.location_analyzer.total_distance)
        self.summarizer.add_activity_datum(self.current_activity_id, self.current_activity_type, self.current_activity_start_time, Keys.APP_AVG_SPEED_KEY, self.location_analyzer.avg_speed)
        self.summarizer.add_activity_data(self.current_activity_id, self.current_activity_type, self.current_activity_start_time, self.location_analyzer.bests)

        self.current_activity_id = None
        self.current_activity_type = None
        self.location_analyzer = None
        self.sensor_analyzers = []

def print_records(store, activity_type):

    # Print title.
    title_str = "Best " + activity_type + " Times:"
    print(title_str)
    print("=" * len(title_str))

    # Print all-time records.
    bests = store.summarizer.get_record_dictionary(activity_type)
    if len(bests) > 0:
        for key in bests:
            print(key + " = " + str(bests[key]))
    else:
        print("none")
    print("\n")

    # Print annual records.
    years = store.summarizer.get_annual_record_years(activity_type)
    for year in years:
        print str(year) + ":"
        bests = store.summarizer.get_annual_record_dictionary(activity_type, year)
        if len(bests) > 0:
            for key in bests:
                print(key + " = " + str(bests[key]))
        else:
            print("none")
        print("\n")

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
    total_time = 0
    num_files_processed = 0
    for subdir, _, files in os.walk(test_dir):

        title_str = "Processing all files in " + test_dir + ":"
        print(title_str + "\n")
        for current_file in files:

            # My test file repo has a description file that we should skip.
            if current_file == "description.csv":
                continue

            full_path = os.path.join(subdir, current_file)
            _, temp_file_ext = os.path.splitext(full_path)
            if temp_file_ext in ['.gpx', '.tcx', '.csv']:
                title_str = "Processing: " + full_path
                print("=" * len(title_str))
                print(title_str)
                print("=" * len(title_str))
                start_time = time.time()
                success, device_id, activity_id = importer.import_file("test user", "", full_path, temp_file_ext)
                if success:
                    elapsed_time = time.time() - start_time
                    total_time = total_time + elapsed_time
                    num_files_processed = num_files_processed + 1
                    print("Elapsed Processing Time: " + str(elapsed_time) + " seconds")
                    print("Success!\n")
                    successes.append(current_file)
                else:
                    print("Failure!\n")
                    failures.append(current_file)

    # Print the summary data.
    print_records(store, Keys.TYPE_RUNNING_KEY)
    print_records(store, Keys.TYPE_CYCLING_KEY)
    print_records(store, Keys.TYPE_SWIMMING_KEY)

    # Print the success and failure summary.
    title_str = "Summary:"
    print(title_str)
    print("=" * len(title_str))
    print("Num success: " + str(len(successes)))
    print("Num failures: " + str(len(failures)))
    for failure in failures:
        print("- " + failure)

    # Print the time summary.
    if num_files_processed > 0:
        print("Average time per sample: " + str(total_time / num_files_processed) + " seconds\n")
    else:
        print("No files processed.\n")

if __name__ == "__main__":
    main()
