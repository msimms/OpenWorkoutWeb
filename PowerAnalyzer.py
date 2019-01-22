# Copyright 2018 Michael J Simms

import inspect
import os
import sys

import Keys
import SensorAnalyzer
import Units

# Locate and load the statistics module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import statistics

class PowerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on power data."""

    def __init__(self, activity_type):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_POWER_KEY, Units.get_power_units_str(), activity_type)
        self.np_buf = []
        self.current_30_sec_buf = []
        self.current_30_sec_buf_start_time = 0

    def do_power_record_check(self, record_name, watts):
        """Looks up the existing record and, if necessary, updates it."""
        old_value = self.get_best_time(record_name)
        if old_value is None or watts > old_value:
            self.bests[record_name] = watts

    def append_sensor_value(self, date_time, value):
        """Adds another reading to the analyzer."""
        SensorAnalyzer.SensorAnalyzer.append_sensor_value(self, date_time, value)

        sum_of_readings = 0
        num_readings = 0
        duration = self.end_time - self.start_time

        # Update the buffers needed for the normalized power calculation.
        if date_time - self.current_30_sec_buf_start_time > 30000:
            if len(self.current_30_sec_buf) > 0:
                self.np_buf.append(statistics.mean(self.current_30_sec_buf))
                self.current_30_sec_buf = []
            self.current_30_sec_buf_start_time = date_time
        self.current_30_sec_buf.append(value)

        # Search for best efforts.
        for reading in reversed(self.readings):
            reading_time = reading[0]
            sum_of_readings = sum_of_readings + reading[1]
            num_readings = num_readings + 1
            curr_time_diff = (self.end_time - reading_time) / 1000
            if curr_time_diff == 5:
                average_power = sum_of_readings / num_readings
                self.do_power_record_check(Keys.BEST_5_SEC_POWER, average_power)
                if duration < 1200:
                    return
            elif curr_time_diff == 1200:
                average_power = sum_of_readings / num_readings
                self.do_power_record_check(Keys.BEST_20_MIN_POWER, average_power)
                if duration < 3600:
                    return
            elif curr_time_diff == 3600:
                average_power = sum_of_readings / num_readings
                self.do_power_record_check(Keys.BEST_1_HOUR_POWER, average_power)
            elif curr_time_diff > 3600:
                return

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = SensorAnalyzer.SensorAnalyzer.analyze(self)
        if len(self.readings) > 0:
            
            results[Keys.MAX_POWER] = self.max
            results[Keys.AVG_POWER] = self.avg

            #
            # Compute normalized power.
            #

            if len(self.np_buf) > 0:

                # Throw away the first 30 second average.
                self.np_buf.pop(0)

                # Raise all items to the fourth power.
                for idx, item in enumerate(self.np_buf):
                    item = pow(item, 4)
                    self.np_buf[idx] = item

                # Average the values that were raised to the fourth.
                np = statistics.mean(self.np_buf)

                # Take the fourth root.
                results[Keys.NORMALIZED_POWER] = pow(np, 0.25)

            #
            # Compute the intensity factory (IF = NP / FTP).
            #

        return results
