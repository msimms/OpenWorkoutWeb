# Copyright 2018 Michael J Simms

import SensorAnalyzer
import StraenKeys

class PowerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on power data."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, StraenKeys.APP_POWER_KEY)
