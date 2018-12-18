# Copyright 2018 Michael J Simms

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
    """Class for performing calculations on bicycle cadence."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_ACCELEROMETER_KEY, "")
        self.x = []
        self.y = []
        self.z = []

    def append_sensor_value(self, date_time, value):
        """Adds another reading to the analyzer."""
        if len(value) != 3:
            return
        self.x.append(value[0])
        self.y.append(value[1])
        self.z.append(value[2])

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        peak_list = peaks.find_peaks_in_numeric_array(self.x, 2.0)
        results[Keys.REPS] = len(peak_list)
#        peak_list = peaks.find_peaks_in_numeric_array(self.y, 2.0)
#        peak_list = peaks.find_peaks_in_numeric_array(self.z, 2.0)
        return results
