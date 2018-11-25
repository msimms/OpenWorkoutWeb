# Copyright 2018 Michael J Simms

import Keys
import SensorAnalyzer
import Units

class CadenceAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on bicycle cadence."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_CADENCE_KEY, Units.get_cadence_units_str())

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        results[Keys.MAX_CADENCE] = self.max
        results[Keys.AVG_CADENCE] = self.avg
        return results
