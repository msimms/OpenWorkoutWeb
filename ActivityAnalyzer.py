# Copyright 2018 Michael J Simms
"""Handles computationally expensive analysis tasks"""

import threading
import time
import Keys
import LocationAnalyzer
import SensorAnalyzerFactory

class ActivityAnalyzer(threading.Thread):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self, activity, activity_id):
        threading.Thread.__init__(self)
        self.activity = activity
        self.activity_id = activity_id
        self.summary_data = None
        self.speed_graph = None
        self.quitting = False

    def terminate(self):
        """Destructor"""
        print("Terminating an analysis worker")

    def run(self):
        """Main run loop."""

        # Load the activity from the database.
        if self.activity is not None:
            self.summary_data = {}

            # Determine the activity type.
            if Keys.ACTIVITY_TYPE_KEY in self.activity:
                activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
            else:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY

            # Check for interrupt.
            if self.quitting:
                return

            # Do the location analysis.
            if Keys.ACTIVITY_LOCATIONS_KEY in self.activity:
                location_analyzer = LocationAnalyzer.LocationAnalyzer(activity_type)
                locations = self.activity[Keys.ACTIVITY_LOCATIONS_KEY]
                for location in locations:
                    date_time = location[Keys.LOCATION_TIME_KEY]
                    latitude = location[Keys.LOCATION_LAT_KEY]
                    longitude = location[Keys.LOCATION_LON_KEY]
                    altitude = location[Keys.LOCATION_ALT_KEY]
                    location_analyzer.append_location(date_time, latitude, longitude, altitude)
                    location_analyzer.update_speeds()
                    time.sleep(0)
                self.summary_data.update(location_analyzer.analyze())

            # Check for interrupt.
            if self.quitting:
                return

            # Do the sensor analysis.
            sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
            for sensor_type in sensor_types_to_analyze:
                if sensor_type in self.activity:
                    sensor_analyzer = SensorAnalyzerFactory.create_with_data(sensor_type, self.activity[sensor_type])
                    self.summary_data.update(sensor_analyzer.analyze())
                    time.sleep(0)

            # Create a current speed graph - if one has not already been created.
            if Keys.APP_CURRENT_SPEED_KEY not in self.activity:
                self.speed_graph = location_analyzer.create_speed_graph()

def main():
    """Entry point for an analysis worker."""

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--msgqueue", default="", help="Address of the message queue", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)
