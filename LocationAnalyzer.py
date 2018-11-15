# Copyright 2018 Michael J Simms

import inspect
import os
import sys
import Keys
import SensorAnalyzer
import Units

# Locate and load the distance module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import distance


class LocationAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on a location track."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_DISTANCE_KEY, Units.get_speed_units_str(Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS))

        self.start_time = None
        self.last_time = None
        self.last_lat = None
        self.last_lon = None
        self.last_alt = None

        self.distance_buf = [] # Holds the distance calculations; used for the current speed calcuations
        self.speed_graph = [] # Holds the current speed calculations 
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.total_vertical = 0.0 # Total ascent (in meters)

        self.avg_speed = None # Average speed (in meters/second)
        self.current_speed = None # Current speed (in meters/second)
        self.best_speed = None # Best speed (in meters/second)

    def update_average_speed(self, date_time):
        """Computes the average speed of the workout. Called by 'append_location'."""
        elapsed_milliseconds = date_time - self.start_time
        if elapsed_milliseconds > 0:
            self.avg_speed = self.total_distance / (elapsed_milliseconds / 1000.0)

    def do_record_check(self, record_name, seconds, meters, record_meters):
        """Looks up the existing record and, if necessary, updates it."""
        if int(meters) == int(record_meters):
            old_value = self.get_best_time(record_name)
            if old_value is None or seconds < old_value:
                self.bests[record_name] = seconds

    def update_speeds(self):
        """Computes the average speed over the last mile. Called by 'append_location'."""

        # This will be recomputed here, so zero it out.
        self.current_speed = 0.0

        # Loop through the list, in reverse order, updating the current speed, and all "bests".
        for time_distance_pair in reversed(self.distance_buf):

            # Convert time from ms to seconds - seconds from this point to the end of the activity.
            total_seconds = (self.last_time - time_distance_pair[0]) / 1000.0
            if total_seconds <= 0:
                continue

            # Distance travelled from this point to the end of the activity.
            total_meters = self.total_distance - time_distance_pair[2]

            # Current speed is the average of the last ten seconds.
            if int(total_seconds) == 7 or self.current_speed is None:
                self.current_speed = total_meters / total_seconds
                if self.best_speed is None or self.current_speed > self.best_speed:
                    self.best_speed = self.current_speed
                if self.total_distance < 1000:
                    break
                self.speed_graph.insert(0, self.current_speed)

            # Is this a new kilometer record for this activity?
            self.do_record_check(Keys.BEST_1K, total_seconds, total_meters, 1000)

            # Is this a new mile record for this activity?
            if total_meters < Units.METERS_PER_MILE:
                continue
            self.do_record_check(Keys.BEST_MILE, total_seconds, total_meters, Units.METERS_PER_MILE)

            # Is this a new 5K record for this activity?
            if total_meters < 5000:
                continue
            self.do_record_check(Keys.BEST_5K, total_seconds, total_meters, 5000)

            # Is this a new 10K record for this activity?
            if total_meters < 10000:
                continue
            self.do_record_check(Keys.BEST_10K, total_seconds, total_meters, 10000)

            # Is this a new 15K record for this activity?
            if total_meters < 15000:
                continue
            self.do_record_check(Keys.BEST_15K, total_seconds, total_meters, 15000)

            # Is this a new metric century record for this activity?
            if total_meters < 100000:
                continue
            self.do_record_check(Keys.BEST_METRIC_CENTURY, total_seconds, total_meters, 100000)

            # Is this a new century record for this activity?
            if total_meters < Units.METERS_PER_MILE * 100.0:
                continue
            self.do_record_check(Keys.BEST_CENTURY, total_seconds, total_meters, Units.METERS_PER_MILE * 100.0)

    def append_location(self, date_time, latitude, longitude, altitude):
        """Adds another location to the analyzer. Locations should be sent in order."""

        # Not much we can do with the first location other than note the start time.
        if self.start_time is None:
            self.start_time = date_time

        # Update the total distance calculation.
        elif self.last_time is not None:
            meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)
            self.total_distance = self.total_distance + meters_traveled
            self.distance_buf.append([date_time, meters_traveled, self.total_distance])
            self.total_vertical = self.total_vertical + abs(altitude - self.last_alt)
            self.update_average_speed(date_time)
            self.update_speeds()

        self.last_time = date_time
        self.last_lat = latitude
        self.last_lon = longitude
        self.last_alt = altitude

    def append_locations(self, locations):
        """Adds many locations to the analyzer. Locations should be sent in order."""

        for location in locations:
            date_time = location[Keys.LOCATION_TIME_KEY]
            latitude = location[Keys.LOCATION_LAT_KEY]
            longitude = location[Keys.LOCATION_LON_KEY]
            altitude = location[Keys.LOCATION_ALT_KEY]
            self.append_location(date_time, latitude, longitude, altitude)
