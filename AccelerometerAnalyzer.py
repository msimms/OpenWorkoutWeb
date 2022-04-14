# Copyright 2018 Michael J Simms
"""Performs calculations on accelerometer data."""

import inspect
import math
import os
import sys

import Keys
import SensorAnalyzer

# Locate and load the peaks module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import kmeans
import peaks
import signals

class AccelerometerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on accelerometer data."""

    def __init__(self, activity_type):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_ACCELEROMETER_KEY, "", activity_type)
        self.x = []
        self.y = []
        self.z = []

    def append_sensor_value(self, date_time, values):
        """Adds another reading to the analyzer."""
        if len(values) != 3:
            return
        self.x.append(values[0])
        self.y.append(values[1])
        self.z.append(values[2])

    def append_sensor_value_from_dict(self, values):
        """Adds another reading to the analyzer."""
        self.x.append(float(values[Keys.ACCELEROMETER_AXIS_NAME_X]))
        self.y.append(float(values[Keys.ACCELEROMETER_AXIS_NAME_Y]))
        self.z.append(float(values[Keys.ACCELEROMETER_AXIS_NAME_Z]))

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)

        # Which axis should we look at?
        if self.activity_type == Keys.TYPE_PUSH_UP_KEY:
            axis_data = self.y
        else:
            axis_data = self.x

        # Smooth the data to take out any jitter.
        smoothed_graph = signals.smooth(axis_data, 4)

        # Search for peaks in the data.
        sets = []
        peak_list = peaks.find_peaks_in_numeric_array_over_threshold(smoothed_graph, 0.2)
        num_peaks = len(peak_list)

        # Need more than one peak to bother doing any further analysis. Also, one or zero will cause a crash, so there's that.
        if num_peaks > 1:

            # Prepare for k-means analysis to find the statistically significant peaks.
            # If there isn't much variation in the data then skip k-means and assume all the peaks are significant.
            areas = []
            area_mean = 0.0
            for peak in peak_list:
                area_mean = area_mean + peak.area
                areas.append(peak.area)
            area_mean = area_mean / len(areas)
            area_stddev = 0.0
            for area in areas:
                area_stddev = area_stddev + ((area - area_mean) * (area - area_mean))
            area_stddev = math.sqrt(area_stddev / (len(areas) - 1))

            # The peaks are all pretty similar, so we'll assume they're all meaningful.
            if area_stddev < 1.0:
                sets.append(len(peak_list))

            # There's a wide range of variation in the peaks, do a k-means analysis so we can get rid of any outliers.
            else:
                significant_peaks = []
                tags = kmeans.kmeans_equally_space_centroids_1_d(areas, 2, 1, len(areas))
                peak_index = 0
                for tag in tags:
                    if tag == 1:
                        significant_peaks.append(peak_list[peak_index])
                    peak_index = peak_index + 1

                sets.append(len(significant_peaks))
        else:
            sets.append(num_peaks)
        results[Keys.APP_SETS_KEY] = sets

        return results
