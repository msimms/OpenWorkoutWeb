# Copyright 2018 Michael J Simms
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
