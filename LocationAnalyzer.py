# Copyright 2018 Michael J Simms

import inspect
import os
import sys
import StraenKeys
import Units

# Locate and load the distance module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import distance

class LocationAnalyzer(object):
    """Class for performing calculations on a location track."""

    def __init__(self):
        super(LocationAnalyzer, self).__init__()
        self.start_time = None
        self.last_time = None
        self.last_lat = None
        self.last_lon = None
        self.last_alt = None
        self.last_total = 0.0

        self.distance_buf = [] # Used for the current speed calcuations
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.total_vertical = 0.0 # Total ascent (in meters)

        self.avg_speed = None # Average speed (in meters/second)
        self.current_speed = None # Current speed (in meters/second)
        self.best_speed = None # Best speed (in meters/second)

        self.best_km = None # Best one kilometer time (in seconds)
        self.best_mile = None # Best one mile time (in seconds)
        self.best_5k = None # Best five kilometer time (in seconds)
        self.best_10k = None # Best ten kilometer time (in seconds)

    def update_average_speed(self, date_time):
        """Computes the average speed of the workout. Called by 'append_location'."""
        elapsed_milliseconds = date_time - self.start_time
        if elapsed_milliseconds > 0:
            self.avg_speed = self.total_distance / (elapsed_milliseconds / 1000.0)

    def do_record_check(self, record, seconds, meters, record_meters):
        if int(meters) == record_meters:
            if record is None or seconds < record:
                record = seconds
        return record

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
            total_meters = self.last_total - time_distance_pair[2]

            # Current speed is the average of the last ten seconds.
            if int(total_seconds) == 10 or self.current_speed is None:
                self.current_speed = total_meters / total_seconds
                if self.best_speed is None or self.current_speed > self.best_speed:
                    self.best_speed = self.current_speed
                if self.last_total < 1000:
                    break

            # Is this a new kilometer record for this activity?
            self.best_km = self.do_record_check(self.best_km, total_seconds, total_meters, 1000)

            # Is this a new mile record for this activity?
            self.best_mile = self.do_record_check(self.best_mile, total_seconds, total_meters, Units.METERS_PER_MILE)

            # Is this a new 5K record for this activity?
            self.best_5k = self.do_record_check(self.best_5k, total_seconds, total_meters, 5000)

            # Is this a new 10K record for this activity?
            self.best_10k = self.do_record_check(self.best_10k, total_seconds, total_meters, 10000)

    def append_location(self, date_time, latitude, longitude, altitude):
        """Adds another location to the analyzer. Locations should be sent in order."""

        # Not much we can do with the first location other than note the start time.
        if self.start_time is None:
            self.start_time = date_time

        # Update the total distance calculation.
        elif self.last_time is not None:
            meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)
            self.last_total = self.last_total + meters_traveled
            self.distance_buf.append([date_time, meters_traveled, self.last_total])
            self.total_distance = self.total_distance + meters_traveled
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
            date_time = location[StraenKeys.LOCATION_TIME_KEY]
            latitude = location[StraenKeys.LOCATION_LAT_KEY]
            longitude = location[StraenKeys.LOCATION_LON_KEY]
            altitude = location[StraenKeys.LOCATION_ALT_KEY]
            self.append_location(date_time, latitude, longitude, altitude)
