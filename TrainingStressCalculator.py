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
"""Encapsulates equations for calculating workout intensity."""

class TrainingStressCalculator(object):
    """Encapsulates equations for calculating workout intensity."""

    def __init__(self):
        super(TrainingStressCalculator, self).__init__()

    @staticmethod
    def estimate_training_stress(workout_duration_secs, avg_workout_pace_meters_per_sec, threshold_pace_meters_per_hour):
        stress = ((workout_duration_secs * avg_workout_pace_meters_per_sec) / threshold_pace_meters_per_hour) * 100.0
        return stress

    @staticmethod
    def calculate_training_stress_from_power(workout_duration_secs, np, ftp):
        # Compute the intensity factor (IF = NP / FTP).
        intfac = np / ftp

        # Compute the training stress score (TSS = (t * NP * IF) / (FTP * 36)).
        tss = (workout_duration_secs * np * intfac) / (ftp * 36)
        return intfac, tss
