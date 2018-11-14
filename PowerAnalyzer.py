# Copyright 2018 Michael J Simms

import SensorAnalyzer
import StraenKeys
import Units

class PowerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on power data."""

    def __init__(self):
        SensorAnalyzer.SensorAnalyzer.__init__(self, StraenKeys.APP_POWER_KEY, Units.get_power_units_str())

    def do_power_record_check(self, record_name, watts):
        """Looks up the existing record and, if necessary, updates it."""
        old_value = self.get_best_time(record_name)
        if old_value is None or watts > old_value:
            self.bests[record_name] = watts

    def append_sensor_value(self, date_time, value):
        """Adds another reading to the analyzer."""
        SensorAnalyzer.SensorAnalyzer.append_sensor_value(self, date_time, value)

        total = 0
        duration = self.end_time - self.start_time

        for reading in reversed(self.readings):
            reading_time = reading[0]
            total = total + reading[1]
            curr_time_diff = (self.end_time - reading_time) / 1000
            if curr_time_diff == 5:
                average_power = total / curr_time_diff
                self.do_power_record_check(StraenKeys.BEST_5_SEC_POWER, average_power)
                if duration < 1200:
                    return
            elif curr_time_diff == 1200:
                average_power = total / curr_time_diff
                self.do_power_record_check(StraenKeys.BEST_20_MIN_POWER, average_power)
                if duration < 3600:
                    return
            elif curr_time_diff == 3600:
                average_power = total / curr_time_diff
                self.do_power_record_check(StraenKeys.BEST_1_HOUR_POWER, average_power)
            elif curr_time_diff > 3600:
                return

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        results[StraenKeys.MAX_POWER] = self.max
        results[StraenKeys.AVG_POWER] = self.avg

        # Compute normalized power.

        # Compute the intensity factory (IF = NP / FTP).

        return results
