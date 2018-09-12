# Copyright 2018 Michael J Simms

import SensorAnalyzer
import StraenKeys
import Units

class HeartRateAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on heart rate data."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, StraenKeys.APP_HEART_RATE_KEY, Units.get_heart_rate_units_str())
