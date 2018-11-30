# Copyright 2018 Michael J Simms

import Keys
import SensorAnalyzer

class AccelerometerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on bicycle cadence."""

    def __init__(self):
        AccelerometerAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_ACCELEROMETER_KEY, "")

    def append_sensor_value(self, date_time, value):
        """Adds another reading to the analyzer."""

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        return results
