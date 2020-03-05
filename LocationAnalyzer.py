# Copyright 2018 Michael J Simms
"""Performs calculations on a location track."""

import inspect
import itertools
import os
import sys
import Keys
import LocationHeatMap
import SensorAnalyzer
import SpeedHeatMap
import Units

# Locate and load the distance module as well as other LibMath modules.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import distance
import kmeans
import peaks
import signals
import statistics

METERS_PER_HALF_MARATHON = 13.1 * Units.METERS_PER_MILE
METERS_PER_MARATHON = 26.2 * Units.METERS_PER_MILE


class LocationAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on a location track."""

    def __init__(self, activity_type):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_DISTANCE_KEY, Units.get_speed_units_str(Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS), activity_type)

        self.activity_type = activity_type
        self.start_time = None
        self.last_time = None
        self.last_lat = None
        self.last_lon = None
        self.last_alt = None

        self.distance_buf = [] # Holds the distance calculations; used for the current speed calcuations. Each item is an array of the form [date_time, meters_traveled, total_distance]
        self.speed_times = [] # Holds the times associated with self.speed_graph
        self.speed_graph = [] # Holds the current speed calculations 
        self.speed_blocks = [] # List of speed/pace blocks, i.e. statistically significant times spent at a given pace
        self.total_distance = 0.0 # Distance traveled (in meters)
        self.total_vertical = 0.0 # Total ascent (in meters)

        self.mile_splits = [] # Mile split times
        self.km_splits = [] # Kilometer split times

        self.avg_speed = None # Average speed (in meters/second)
        self.current_speed = None # Current speed (in meters/second)

        self.location_heat_map = LocationHeatMap.LocationHeatMap()
        self.speed_heat_map = SpeedHeatMap.SpeedHeatMap()

        self.last_speed_buf_update_time = 0

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

    def do_split_check(self, seconds, split_meters, split_buf):
        units_traveled = self.total_distance / split_meters
        whole_units_traveled = int(units_traveled)
        if len(split_buf) < whole_units_traveled + 1:
            split_buf.append(seconds)
        else:
            split_buf[whole_units_traveled] = seconds

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
                if current_time > self.last_speed_buf_update_time:
                    self.speed_times.append(current_time)
                    self.speed_graph.append(self.current_speed)
                    self.speed_heat_map.append(self.current_speed)
                    self.last_speed_buf_update_time = current_time

            # Is this a new kilometer record for this activity?
            if total_meters < 1000:
                continue
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
                if total_meters < METERS_PER_HALF_MARATHON:
                    continue
                self.do_record_check(Keys.BEST_HALF_MARATHON, total_seconds, total_meters, METERS_PER_HALF_MARATHON)

                # Is this a new marathon record for this activity?
                if total_meters < METERS_PER_MARATHON:
                    continue
                self.do_record_check(Keys.BEST_MARATHON, total_seconds, total_meters, METERS_PER_MARATHON)

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

            # How far since the last point?
            meters_traveled = distance.haversine_distance(latitude, longitude, altitude, self.last_lat, self.last_lon, self.last_alt)

            # Update totals and averages.
            self.total_distance = self.total_distance + meters_traveled
            self.distance_buf.append([date_time, meters_traveled, self.total_distance])
            self.total_vertical = self.total_vertical + abs(altitude - self.last_alt)
            self.update_average_speed(date_time)

            # Update the split calculations.
            self.do_split_check(date_time - self.start_time, 1000, self.km_splits)
            self.do_split_check(date_time - self.start_time, Units.METERS_PER_MILE, self.mile_splits)

        # Update the heat map.
        self.location_heat_map.append(latitude, longitude)

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
    
    def examine_peak(self, start_index, end_index):
        """Examines a line of near-constant pace/speed."""
        if start_index >= end_index:
            return

        # How long (in seconds) was this block?
        start_time = self.speed_times[start_index]
        end_time = self.speed_times[end_index]
        line_duration_seconds = end_time - start_time
        line_length_meters = 0
        line_avg_speed = 0.0

        # Don't consider anything less than ten seconds.
        if line_duration_seconds > 10:
            speeds = self.speed_graph[start_index:end_index - 1]
            start_distance_rec = None
            end_distance_rec = None
            for rec in self.distance_buf:
                if rec[0] == start_time:
                    start_distance_rec = rec
                if rec[0] == end_time:
                    end_distance_rec = rec
                    break
            line_length_meters = 0.0
            if start_distance_rec is not None and end_distance_rec is not None:
                line_length_meters = end_distance_rec[2] - start_distance_rec[2]
            line_avg_speed = statistics.mean(speeds)
            self.speed_blocks.append(line_avg_speed)

        return start_time, end_time, line_duration_seconds, line_length_meters, line_avg_speed

    def analyze(self):
        """Called when all location readings have been processed."""

        # Let the base class perform the analysis first.
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)

        # Do pace analysis.
        if len(self.speed_graph) > 1:

            # Compute the speed/pace variation. This will tell us how consistent the pace was.
            speed_variance = statistics.variance(self.speed_graph, self.avg_speed)
            results[Keys.APP_SPEED_VARIANCE_KEY] = speed_variance

            # Smooth the speed graph to take out some of the GPS jitter.
            smoothed_graph = signals.smooth(self.speed_graph, 4)
            if len(smoothed_graph) > 1:
    
                # Find peaks in the speed graph.
                peak_list = peaks.find_peaks_in_numeric_array(smoothed_graph, 0.5)

                # Examine the lines between the peaks.
                all_intervals = []
                for peak in peak_list:
                    interval = self.examine_peak(peak.left_trough.x, peak.right_trough.x)
                    all_intervals.append(interval)

                # Do a k-means analysis on the computed paces blocks so we can get rid of any outliers.
                significant_intervals = []
                tags = kmeans.kmeans_equally_space_centroids_1_d(self.speed_blocks, 2, 1, len(self.speed_blocks))
                interval_index = 0
                for tag in tags:
                    if tag == 1:
                        significant_intervals.append(all_intervals[interval_index])
                    interval_index = interval_index + 1

                results[Keys.ACTIVITY_INTERVALS] = significant_intervals

        # Insert the location into the analysis dictionary so that it gets cached.
        results[Keys.LONGEST_DISTANCE] = self.total_distance

        # Insert the split times.
        results[Keys.MILE_SPLITS] = self.mile_splits
        results[Keys.KM_SPLITS] = self.km_splits

        return results

    def create_speed_graph(self):
        """Returns a list of time, value pairs for speed."""
        graph = []
        if len(self.speed_graph) == len(self.speed_times):
            if sys.version_info[0] < 3:
                zip_func = itertools.izip
            else:
                zip_func = zip
            for time_val, speed_val in zip_func(self.speed_times, self.speed_graph):
                point = []
                point.append(time_val)
                point.append(float(speed_val))
                graph.append(point)
        return graph
