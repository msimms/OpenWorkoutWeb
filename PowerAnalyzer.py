# Copyright 2018 Michael J Simms

import SensorAnalyzer
import StraenKeys

class PowerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on power data."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, StraenKeys.APP_POWER_KEY, "Watts")
        self.best_5_sec_power = 0.0
        self.best_20_min_power = 0.0
        self.best_1_hour_power = 0.0

    def append_sensor_value(self, date_time, value):
        """Adds another reading to the analyzer."""
        SensorAnalyzer.SensorAnalyzer.append_sensor_value(self, date_time, value)

        total = 0
        duration = self.end_time - self.start_time

        for reading in reversed(self.readings):
            reading_time = reading[0]
            total = total + reading[1]
            curr_time_diff = self.end_time - reading_time
            if curr_time_diff == 5:
                average_power = total / curr_time_diff
                if average_power > self.best_5_sec_power:
                    self.best_5_sec_power = average_power
                if duration < 120:
                    return
            elif curr_time_diff == 120:
                average_power = total / curr_time_diff
                if average_power > self.best_20_min_power:
                    self.best_20_min_power = average_power
                if duration < 3600:
                    return
            elif curr_time_diff == 3600:
                average_power = total / curr_time_diff
                if average_power > self.best_1_hour_power:
                    self.best_1_hour_power = average_power
            elif curr_time_diff > 3600:
                return

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)

        # Compute normalized power.

        # Compute the intensity factory (IF = NP / FTP).

        results["5 Sec. Avg. Power"] = self.best_5_sec_power
        results["20 Sec. Avg. Power"] = self.best_20_min_power
        results["1 Hour Avg. Power"] = self.best_1_hour_power
        return results
