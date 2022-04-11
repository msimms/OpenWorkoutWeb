# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Mike Simms
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

class VO2MaxCalculator(object):
    """Estimates VO2Max"""

    def __init__(self):
        super(VO2MaxCalculator, self).__init__()

    @staticmethod
    def estimate_vo2max_from_heart_rate(max_hr, resting_hr):
        if max_hr == None:
            return 0.0
        if resting_hr == None:
            return 0.0
        if resting_hr == 0:
            return 0.0

        return 15.3 * (max_hr / resting_hr)

    @staticmethod
    def estimate_vo2max_from_race_distance_in_meters(race_distance_meters, race_time_minutes):
        if race_distance_meters == None:
            return 0.0
        if race_time_minutes == None:
            return 0.0
        if race_time_minutes == 0:
            return 0.0

        speed = race_distance_meters / race_time_minutes
        vo2max = -4.60 + 0.182258 * speed + 0.000104 * speed * speed
        if vo2max > 100.0:
            raise Exception("Invalid VO2Max.")
        return vo2max
