# Copyright 2018 Michael J Simms

import inspect
import os
import sys

# Locate and load the distance module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import distance

class TrackAnalyzer(object):
    """Class for performing calculations on a location track."""

    def __init__(self):
        super(TrackAnalyzer, self).__init__()
        self.start_time = None
        self.last_time = None
        self.last_lat = None
        self.last_lon = None
        self.last_alt = None
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.avg_speed = 0.0 # Average speed (in meters/second)
        self.current_speed = 0.0 # Current speed (in meters/second)
        self.distance_buf = [] # Used for the current speed calcuation

    def update_current_speed(self, date_time, meters_traveled):
        """Computes the current speed of the workout. Called by 'append_location'."""
        self.distance_buf.append([date_time, meters_traveled])
        if len(self.distance_buf) > 3:
            self.distance_buf.pop(0)

        total = 0.0
        first_time = 0
        for distance in self.distance_buf:
            if first_time == 0:
                first_time = distance[0]
            total = total + distance[1]
        total_time = date_time - first_time
        if total_time > 0:
            self.current_speed = total / total_time

    def update_average_speed(self, date_time):
        """Computes the average speed of the workout. Called by 'append_location'."""
        elapsed_seconds = date_time - self.start_time
        if elapsed_seconds > 0:
            self.avg_speed = self.total_distance / elapsed_seconds

    def append_location(self, date_time, latitude, longitude, altitude):
        """Adds another location to the analyzer. Locations should be sent in order."""

        # Not much we can do with the first location other than note the start time.
        if self.start_time is None:
            self.start_time = date_time

        # Update the total distance calculation.
        elif self.last_lat is not None:
            meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)
            self.total_distance = self.total_distance + meters_traveled
            self.update_current_speed(date_time, meters_traveled)
            self.update_average_speed(date_time)

        self.last_time = date_time
        self.last_lat = latitude
        self.last_lon = longitude
        self.last_alt = altitude
