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
"""Estimates VO2Max."""

import math

class VO2MaxCalculator(object):
    """Estimates VO2Max"""

    def __init__(self):
        super(VO2MaxCalculator, self).__init__()

    @staticmethod
    def estimate_vo2max_from_heart_rate(resting_hr, max_hr):
        if max_hr == None:
            return 0.0
        if resting_hr == None:
            return 0.0
        if resting_hr == 0:
            return 0.0

        vo2max = max_hr / resting_hr * 15.4
        return vo2max

    @staticmethod
    def estimate_vo2max_from_race_distance_in_meters(race_distance_meters, race_time_secs):
        """Daniels and Gilbert VO2 Max formula"""
        if race_distance_meters == None:
            return 0.0
        if race_time_secs == None:
            return 0.0
        if race_time_secs == 0:
            return 0.0

        t = race_time_secs / 60
        v = race_distance_meters / t
        vo2max = (-4.60 + 0.182258 * v + 0.000104 * math.pow(v, 2.0)) / (0.8 + 0.1894393 * math.pow(math.e, -0.012778 * t) + 0.2989558 * math.pow(math.e, -0.1932605 * t))
        if vo2max > 100.0:
            raise Exception("Invalid VO2Max.")
        return vo2max

    @staticmethod
    def estimate_vo2max_from_race_distance_in_meters_and_heart_rate(race_distance_meters, race_time_minutes, load_hr, resting_hr, max_hr):
        return (race_distance_meters / race_time_minutes * 0.2) / ((load_hr - resting_hr) / (max_hr - resting_hr)) + 3.5

    @staticmethod
    def estimate_vo2max_using_cooper_test():
        raise Exception("Unimplemented function.")
