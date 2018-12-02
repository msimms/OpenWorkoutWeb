# Copyright 2018 Michael J Simms

import inspect
import itertools
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
import peaks
import statistics


class LocationAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on a location track."""

    def __init__(self, activity_type):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_DISTANCE_KEY, Units.get_speed_units_str(Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS))

        self.activity_type = activity_type
        self.start_time = None
        self.last_time = None
        self.last_lat = None
        self.last_lon = None
        self.last_alt = None

        self.distance_buf = [] # Holds the distance calculations; used for the current speed calcuations
        self.speed_times = [] # Holds the times associated with self.speed_graph
        self.speed_graph = [] # Holds the current speed calculations 
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.total_vertical = 0.0 # Total ascent (in meters)

        self.avg_speed = None # Average speed (in meters/second)
        self.current_speed = None # Current speed (in meters/second)

        # This refers to the number of seconds used when averaging samples together to
        # compute the current speed. The exact numbers were chosen based on experimentation.
        if activity_type is Keys.TYPE_CYCLING_KEY:
            self.speed_window_size = 7
        else:
            self.speed_window_size = 11

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
            current_time = time_distance_pair[0]
            total_seconds = (self.last_time - current_time) / 1000.0
            if total_seconds <= 0:
                continue

            # Distance travelled from this point to the end of the activity.
            current_distance = time_distance_pair[2]
            total_meters = self.total_distance - current_distance

            # Current speed is the average of the last ten seconds.
            if int(total_seconds) == self.speed_window_size or self.current_speed is None:
                self.current_speed = total_meters / total_seconds
                if Keys.BEST_SPEED not in self.bests or self.current_speed > self.bests[Keys.BEST_SPEED]:
                    self.bests[Keys.BEST_SPEED] = self.current_speed
                if self.total_distance < 1000:
                    break
                self.speed_times.append(current_time)
                self.speed_graph.append(self.current_speed)

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

            # Running-specific records:
            if self.activity_type == Keys.TYPE_RUNNING_KEY:

                # Is this a new 15K record for this activity?
                if total_meters < 15000:
                    continue
                self.do_record_check(Keys.BEST_15K, total_seconds, total_meters, 15000)

                # Is this a new half marathon record for this activity?
                if total_meters < 13.1 * Units.METERS_PER_MILE:
                    continue
                self.do_record_check(Keys.BEST_HALF_MARATHON, total_seconds, total_meters, 13.1 * Units.METERS_PER_MILE)

                # Is this a new marathon record for this activity?
                if total_meters < 26.2 * Units.METERS_PER_MILE:
                    continue
                self.do_record_check(Keys.BEST_MARATHON, total_seconds, total_meters, 26.2 * Units.METERS_PER_MILE)

            # Cycling-specific records:
            if self.activity_type == Keys.TYPE_CYCLING_KEY:

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
    
    def check_pace_line(self, peak_list, start_index, end_index):
        """Examines a line of near-constant pace/speed."""
        if start_index >= end_index:
            return

        start_time = self.speed_times[start_index]
        end_time = self.speed_times[end_index]
        line_duration = end_time - start_time
        if line_duration > 60000:
            speeds = self.speed_graph[start_index:end_index - 1]
            avg_speed = statistics.mean(speeds)
            avg_pace = Units.meters_per_sec_to_minutes_per_mile(avg_speed)

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)

        # Do pace analysis.
        if len(self.speed_graph) > 1:

            # Find peaks in the speed graph.
            peak_list = peaks.find_peaks_in_numeric_array(self.speed_graph, 2.0)

            # Examine the lines between the peaks.
            last_peak_index = 0
            for peak in peak_list:
                peak_index = peak.left_trough.x
                self.check_pace_line(peak_list, last_peak_index, peak_index)
                last_peak_index = peak_index + 1
            self.check_pace_line(peak_list, last_peak_index, len(self.speed_graph) - 1)
        return results

    def create_speed_graph(self):
        """Returns a list of time, value pairs for speed."""
        graph = []
        if len(self.speed_graph) == len(self.speed_times):
            for time_val, speed_val in itertools.izip(self.speed_times, self.speed_graph):
                point = []
                point.append(time_val)
                point.append(float(speed_val))
                graph.append(point)
        return graph
