# Copyright 2018 Michael J Simms

import Keys
import AccelerometerAnalyzer
import CadenceAnalyzer
import HeartRateAnalyzer
import PowerAnalyzer

def supported_sensor_types():
    return [Keys.APP_ACCELEROMETER_KEY, Keys.APP_CADENCE_KEY, Keys.APP_HEART_RATE_KEY, Keys.APP_POWER_KEY]

def create(sensor_type):
    """Creates a sensor analyzer object of the specified type."""
    sensor_analyzer = None
    if sensor_type == Keys.APP_ACCELEROMETER_KEY:
        sensor_analyzer = AccelerometerAnalyzer.AccelerometerAnalyzer()
    elif sensor_type == Keys.APP_CADENCE_KEY:
        sensor_analyzer = CadenceAnalyzer.CadenceAnalyzer()
    elif sensor_type == Keys.APP_HEART_RATE_KEY:
        sensor_analyzer = HeartRateAnalyzer.HeartRateAnalyzer()
    elif sensor_type == Keys.APP_POWER_KEY:
        sensor_analyzer = PowerAnalyzer.PowerAnalyzer()
    return sensor_analyzer

def create_with_data(sensor_type, data):
    """Creates a sensor analyzer object of the specified type and loads it with the given data."""
    sensor_analyzer = create(sensor_type)
    if sensor_analyzer is not None:
        if sensor_type == Keys.APP_ACCELEROMETER_KEY:
            for datum in data:
                sensor_analyzer.append_sensor_value_from_dict(datum)
        else:
            for datum in data:
                time = int(datum.keys()[0])
                value = float(datum.values()[0])
                sensor_analyzer.append_sensor_value(time, value)
    return sensor_analyzer
