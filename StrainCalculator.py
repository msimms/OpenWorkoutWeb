# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Mike Simms
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
"""Encapsulates equations for calculating or estimating the strain the workout places on the body."""

class StrainCalculator(object):
    """Encapsulates equations for calculating or estimating the strain the workout places on the body."""

    def __init__(self):
        super(StrainCalculator, self).__init__()

    @staticmethod
    def estimate_strain_score(workout_duration_secs, avg_workout_pace_meters_per_sec, threshold_pace_meters_per_hour):
        strain_score = ((workout_duration_secs * avg_workout_pace_meters_per_sec) / threshold_pace_meters_per_hour) * 100.0
        return strain_score

    @staticmethod
    def calculate_strain_score_from_power(workout_duration_secs, np, ftp):
        # Sanity check.
        if ftp is None or ftp < 0.1:
            return 0.0

        # Compute the strain score: (t * NP * IF) / (FTP * 36).
        strain_score = (workout_duration_secs * (np / ftp) * (np / ftp)) / (ftp * 36)
        return strain_score
