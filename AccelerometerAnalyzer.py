# Copyright 2018 Michael J Simms
"""Performs calculations on accelerometer data."""

import inspect
import os
import sys

import Keys
import SensorAnalyzer

# Locate and load the peaks module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import peaks

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
        peak_list = peaks.find_peaks_in_numeric_array(self.x, 1.0)

        sets = []
        sets.append(len(peak_list))
        results[Keys.APP_SETS_KEY] = sets
        return results
