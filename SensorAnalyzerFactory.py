# Copyright 2018 Michael J Simms

import StraenKeys
import HeartRateAnalyzer
import PowerAnalyzer

class SensorAnalyzerFactory(object):
    """Class for creating sensor analyzer objects (heart rate, power, etc.)."""

    def __init__(self):
        super(SensorAnalyzerFactory, self).__init__()

    def create(self, sensor_type):
        """Creates a sensor analyzer object of the specified type."""
        sensor_analyzer = None
        if sensor_type == StraenKeys.APP_HEART_RATE_KEY:
            sensor_analyzer = HeartRateAnalyzer.HeartRateAnalyzer()
        elif sensor_type == StraenKeys.APP_POWER_KEY:
            sensor_analyzer = PowerAnalyzer.PowerAnalyzer()
        return sensor_analyzer
