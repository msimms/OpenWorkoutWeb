# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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
"""Performs calculations on bicycle cadence."""

import Keys
import SensorAnalyzer
import Units

class CadenceAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on bicycle cadence."""

    def __init__(self, activity_type):
        self.is_foot_based_activity = activity_type in Keys.FOOT_BASED_ACTIVITIES
        if self.is_foot_based_activity:
            self.key = Keys.STEPS_PER_MINUTE
            self.units = Units.get_running_cadence_units_str()
        else:
            self.key = Keys.APP_CADENCE_KEY
            self.units = Units.get_cadence_units_str()
        SensorAnalyzer.SensorAnalyzer.__init__(self, self.key, self.units, activity_type)

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        if len(self.readings) > 0:
            if self.is_foot_based_activity:
                results[Keys.MAX_CADENCE] = self.max * 2.0
                results[Keys.AVG_CADENCE] = self.avg * 2.0
            else:
                results[Keys.MAX_CADENCE] = self.max
                results[Keys.AVG_CADENCE] = self.avg
        return results
