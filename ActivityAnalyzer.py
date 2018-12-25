# Copyright 2018 Michael J Simms
"""Handles computationally expensive analysis tasks"""

import threading
import time
import DataMgr
import Keys
import LocationAnalyzer
import SensorAnalyzerFactory

class ActivityAnalyzer(threading.Thread):
    """Class for scheduling computationally expensive analysis tasks."""

    def __init__(self, data_mgr, activity_id):
        threading.Thread.__init__(self)
        self.data_mgr = data_mgr
        self.activity_id = activity_id
        self.quitting = False

    def terminate(self):
        """Destructor"""
        print("Terminating an analysis worker")

    def run(self):
        """Main run loop."""

        # Load the activity from the database.
        activity = self.data_mgr.retrieve_activity(self.activity_id)
        if activity is not None:
            summary_data = {}

            # Determine the activity type.
            if Keys.ACTIVITY_TYPE_KEY in activity:
                activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
            else:
                activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY

            # Check for interrupt.
            if self.quitting:
                return

            # Do the location analysis.
            if Keys.ACTIVITY_LOCATIONS_KEY in activity:
                location_analyzer = LocationAnalyzer.LocationAnalyzer(activity_type)
                locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
                for location in locations:
                    date_time = location[Keys.LOCATION_TIME_KEY]
                    latitude = location[Keys.LOCATION_LAT_KEY]
                    longitude = location[Keys.LOCATION_LON_KEY]
                    altitude = location[Keys.LOCATION_ALT_KEY]
                    location_analyzer.append_location(date_time, latitude, longitude, altitude)
                    location_analyzer.update_speeds()
                    time.sleep(0)
                summary_data.update(location_analyzer.analyze())

            # Check for interrupt.
            if self.quitting:
                return

            # Do the sensor analysis.
            sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
            for sensor_type in sensor_types_to_analyze:
                if sensor_type in activity:
                    sensor_analyzer = SensorAnalyzerFactory.create_with_data(sensor_type, activity[sensor_type])
                    summary_data.update(sensor_analyzer.analyze())
                    time.sleep(0)

            # Save the summary results.
            self.data_mgr.create_activity_summary(self.activity_id, summary_data)

            # Save the current speed graph.
            if Keys.APP_CURRENT_SPEED_KEY not in activity:
                speed_graph = location_analyzer.create_speed_graph()
                self.data_mgr.create_metadata_list(self.activity_id, Keys.APP_CURRENT_SPEED_KEY, speed_graph)

def main():
    """Entry point for an analysis worker."""
    pass
