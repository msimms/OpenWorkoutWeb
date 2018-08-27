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
        self.avg_speed = 0.0 # Average sppeed (in meters/second)

    def update_current_speed(self):
        """Computes the current speed of the workout. Called by 'append_location'."""
        pass

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

            self.update_current_speed()
            self.update_average_speed(date_time)

        self.last_time = date_time
        self.last_lat = latitude
        self.last_lon = longitude
        self.last_alt = altitude
