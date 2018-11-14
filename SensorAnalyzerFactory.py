# Copyright 2018 Michael J Simms

import Keys
import CadenceAnalyzer
import HeartRateAnalyzer
import PowerAnalyzer

class SensorAnalyzerFactory(object):
    """Class for creating sensor analyzer objects (heart rate, power, etc.)."""

    def __init__(self):
        super(SensorAnalyzerFactory, self).__init__()

    def create(self, sensor_type):
        """Creates a sensor analyzer object of the specified type."""
        sensor_analyzer = None
        if sensor_type == Keys.APP_CADENCE_KEY:
            sensor_analyzer = CadenceAnalyzer.CadenceAnalyzer()
        elif sensor_type == Keys.APP_HEART_RATE_KEY:
            sensor_analyzer = HeartRateAnalyzer.HeartRateAnalyzer()
        elif sensor_type == Keys.APP_POWER_KEY:
            sensor_analyzer = PowerAnalyzer.PowerAnalyzer()
        return sensor_analyzer

    def create_with_data(self, sensor_type, data):
        """Creates a sensor analyzer object of the specified type and loads it with the given data."""
        sensor_analyzer = self.create(sensor_type)
        if sensor_analyzer is not None:
            for datum in data:
                time = int(datum.keys()[0])
                value = float(datum.values()[0])
                sensor_analyzer.append_sensor_value(time, value)
        return sensor_analyzer
