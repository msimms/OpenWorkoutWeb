# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Michael J Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Instantiates objects that can analyze sensor data."""

import sys
import Keys
import AccelerometerAnalyzer
import CadenceAnalyzer
import HeartRateAnalyzer
import PowerAnalyzer

def supported_sensor_types():
    return [Keys.APP_ACCELEROMETER_KEY, Keys.APP_CADENCE_KEY, Keys.APP_HEART_RATE_KEY, Keys.APP_POWER_KEY]

def create(sensor_type, activity_type, activity_user_id, data_mgr, user_mgr):
    """Creates a sensor analyzer object of the specified type."""
    sensor_analyzer = None
    if sensor_type == Keys.APP_ACCELEROMETER_KEY:
        sensor_analyzer = AccelerometerAnalyzer.AccelerometerAnalyzer(activity_type)
    elif sensor_type == Keys.APP_CADENCE_KEY:
        sensor_analyzer = CadenceAnalyzer.CadenceAnalyzer(activity_type)
    elif sensor_type == Keys.APP_HEART_RATE_KEY:
        sensor_analyzer = HeartRateAnalyzer.HeartRateAnalyzer(activity_type)
    elif sensor_type == Keys.APP_POWER_KEY:
        sensor_analyzer = PowerAnalyzer.PowerAnalyzer(activity_type, activity_user_id, data_mgr, user_mgr)
    return sensor_analyzer

def create_with_data(sensor_type, data, activity_type, activity_user_id, data_mgr, user_mgr):
    """Creates a sensor analyzer object of the specified type and loads it with the given data."""
    sensor_analyzer = create(sensor_type, activity_type, activity_user_id, data_mgr, user_mgr)
    if sensor_analyzer is not None:
        if sensor_type == Keys.APP_ACCELEROMETER_KEY:
            for datum in data:
                sensor_analyzer.append_sensor_value_from_dict(datum)
        else:
            for datum in data:
                time = int(float(list(datum.keys())[0]))
                value = float(list(datum.values())[0])
                sensor_analyzer.append_sensor_value(time, value)
    return sensor_analyzer
