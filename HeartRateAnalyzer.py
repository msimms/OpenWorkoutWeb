# Copyright 2018 Michael J Simms

import Keys
import SensorAnalyzer
import Units

class HeartRateAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on heart rate data."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_HEART_RATE_KEY, Units.get_heart_rate_units_str())

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        if len(self.readings) > 0:
            results[Keys.MAX_HEART_RATE] = self.max
            results[Keys.AVG_HEART_RATE] = self.avg
        return results
