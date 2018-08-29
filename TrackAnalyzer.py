# Copyright 2018 Michael J Simms

import inspect
import os
import sys

# Locate and load the distance module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import distance

METERS_PER_MILE = 1609.34

class TrackAnalyzer(object):
    """Class for performing calculations on a location track."""

    def __init__(self):
        super(TrackAnalyzer, self).__init__()
        self.start_time = None
        self.last_time = None
        self.last_lat = None
        self.last_lon = None
        self.last_alt = None
        self.distance_buf = [] # Used for the current speed calcuations
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.avg_speed = 0.0 # Average speed (in meters/second)
        self.current_speed = 0.0 # Current speed (in meters/second)
        self.best_km = 0.0 # Best one kilometer average speed
        self.best_mile = 0.0 # Best one mile average speed

    def update_average_speed(self, date_time):
        """Computes the average speed of the workout. Called by 'append_location'."""
        elapsed_seconds = date_time - self.start_time
        if elapsed_seconds > 0:
            self.avg_speed = self.total_distance / elapsed_seconds

    def update_speeds(self, date_time, meters_traveled):
        """Computes the average speed over the last mile. Called by 'append_location'."""

        # Save the most recent time and distance calculation.
        self.distance_buf.append([date_time, meters_traveled])

        # Loop through the list, in reverse order, updating the current speed, and all "bests"
        distance_sum = 0.0
        first_time = 0
        last_time = 0
        last_km_speed = 0.0
        last_mile_speed = 0.0
        self.current_speed = 0.0
        for time_distance_pair in reversed(self.distance_buf):
            if last_time == 0:
                last_time = time_distance_pair[0]
            first_time = time_distance_pair[0]
            distance_sum = distance_sum + time_distance_pair[1]
            total_time = last_time - first_time

            # Divide by zero check for the first iteration.
            if total_time > 0:

                # Average speed over the given distance.
                speed = distance_sum / total_time

                # Current speed is the average of the last three seconds.
                if self.current_speed == 0.0 and total_time > 3:
                    self.current_speed = speed

                # Is this a new kilometer record for this activity?
                if distance_sum > 1000 and last_km_speed == 0.0:
                    last_km_speed = speed
                    if last_km_speed > self.best_km:
                        self.best_km = last_km_speed

                # Is this a new mile record for this activity?
                if distance_sum > METERS_PER_MILE and last_mile_speed == 0.0:
                    last_mile_speed = speed
                    if last_mile_speed > self.best_mile:
                        self.best_mile = last_mile_speed
                    break # A mile is the longest distance we're looking for so just break

    def append_location(self, date_time, latitude, longitude, altitude):
        """Adds another location to the analyzer. Locations should be sent in order."""

        # Not much we can do with the first location other than note the start time.
        if self.start_time is None:
            self.start_time = date_time

        # Update the total distance calculation.
        elif self.last_lat is not None:
            meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)
            self.total_distance = self.total_distance + meters_traveled
            self.update_average_speed(date_time)
            self.update_speeds(date_time, meters_traveled)

        self.last_time = date_time
        self.last_lat = latitude
        self.last_lon = longitude
        self.last_alt = altitude
