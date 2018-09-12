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
        self.distance_buf = [] # Used for the current speed calcuations
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.avg_speed = 0.0 # Average speed (in meters/second)
        self.current_speed = 0.0 # Current speed (in meters/second)
        self.best_speed = 0.0 # Best speed (in meters/second)
        self.best_km = 0.0 # Best one kilometer average speed (in meters/second)
        self.best_mile = 0.0 # Best one mile average speed (in meters/second)
        self.distance_units = Units.UNITS_DISTANCE_METERS
        self.time_units = Units.UNITS_TIME_SECONDS

    def update_average_speed(self, date_time):
        """Computes the average speed of the workout. Called by 'append_location'."""
        elapsed_seconds = date_time - self.start_time
        if elapsed_seconds > 0:
            self.avg_speed = self.total_distance / elapsed_seconds

    def update_speeds(self):
        """Computes the average speed over the last mile. Called by 'append_location'."""

        total_meters = 0.0
        last_km_speed = 0.0
        last_mile_speed = 0.0
        self.current_speed = 0.0

        # Loop through the list, in reverse order, updating the current speed, and all "bests".
        for time_distance_pair in reversed(self.distance_buf):
            total_meters = total_meters + time_distance_pair[1]
            total_time = self.last_time - time_distance_pair[0]

            # Divide by zero check.
            if total_time > 0:

                # Average speed over the given distance.
                total_seconds = total_time / 1000.0
                speed = total_meters / total_seconds

                # Current speed is the average of the last three seconds.
                if self.current_speed == 0.0 and int(total_seconds) == 3:
                    self.current_speed = speed
                    if self.current_speed > self.best_speed:
                        self.best_speed = self.current_speed

                # Is this a new kilometer record for this activity?
                if int(total_meters) == 1000 and last_km_speed == 0.0:
                    last_km_speed = speed
                    if last_km_speed > self.best_km:
                        self.best_km = last_km_speed

                # Is this a new mile record for this activity?
                elif int(total_meters) == int(Units.METERS_PER_MILE) and last_mile_speed == 0.0:
                    last_mile_speed = speed
                    if last_mile_speed > self.best_mile:
                        self.best_mile = last_mile_speed

                # A mile is the longest distance we're looking for, so just break.
                elif int(total_meters) > Units.METERS_PER_MILE:
                    break

    def append_location(self, date_time, latitude, longitude, altitude):
        """Adds another location to the analyzer. Locations should be sent in order."""

        # Not much we can do with the first location other than note the start time.
        if self.start_time is None:
            self.start_time = date_time

        # Update the total distance calculation.
        elif self.last_time is not None:
            meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)
            self.distance_buf.append([date_time, meters_traveled])
            self.total_distance = self.total_distance + meters_traveled

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

            if self.start_time is None:
                self.start_time = date_time
            elif self.last_time is not None:
                meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)
                self.distance_buf.append([date_time, meters_traveled])
                self.total_distance = self.total_distance + meters_traveled

                self.update_average_speed(date_time)
                self.update_speeds()

            self.last_time = date_time
            self.last_lat = latitude
            self.last_lon = longitude
            self.last_alt = altitude
