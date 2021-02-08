# Copyright 2018 Michael J Simms
"""Performs calculations on power data."""

import inspect
import os
import sys

import DataMgr
import FtpCalculator
import Keys
import SensorAnalyzer
import StrainCalculator
import Units

class PowerAnalyzer(SensorAnalyzer.SensorAnalyzer):
    """Class for performing calculations on power data."""

    def __init__(self, activity_type, activity_user_id, data_mgr):
        SensorAnalyzer.SensorAnalyzer.__init__(self, Keys.APP_POWER_KEY, Units.get_power_units_str(), activity_type)
        self.data_mgr = data_mgr
        self.np_buf = []
        self.current_30_sec_buf = []
        self.current_30_sec_buf_start_time = 0
        self.activity_user_id = activity_user_id

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
                avg_norm_power = sum(self.current_30_sec_buf) / len(self.current_30_sec_buf)
                self.np_buf.append(avg_norm_power)
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
                if duration < 720:
                    return
            elif curr_time_diff == 720:
                average_power = sum_of_readings / num_readings
                self.do_power_record_check(Keys.BEST_12_MIN_POWER, average_power)
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

            if len(self.np_buf) > 1:

                # Throw away the first 30 second average.
                self.np_buf.pop(0)

                # Needs this for the variability index calculation.
                ap = sum(self.np_buf) / len(self.np_buf)

                # Raise all items to the fourth power.
                for idx, item in enumerate(self.np_buf):
                    item = pow(item, 4)
                    self.np_buf[idx] = item

                # Average the values that were raised to the fourth.
                ap2 = sum(self.np_buf) / len(self.np_buf)

                # Take the fourth root.
                np = pow(ap2, 0.25)
                results[Keys.NORMALIZED_POWER] = np

                # Compute the variability index (VI = NP / AP).
                vi  = np / ap
                results[Keys.VARIABILITY_INDEX] = vi

                # Additional calculations if we have the user's FTP.
                if self.activity_user_id and self.data_mgr:

                    # Get the user's FTP.
                    ftp = self.data_mgr.retrieve_user_estimated_ftp(self.activity_user_id)
                    if ftp is not None:

                        # Compute the strain score.
                        t = (self.end_time - self.start_time) / 1000.0
                        calc = StrainCalculator.StrainCalculator()
                        strain_score = calc.calculate_strain_score_from_power(t, np, ftp[0])
                        results[Keys.STRAIN_SCORE] = strain_score

            #
            # Compute the threshold power from this workout. Maybe we have a new estimated FTP?
            #

            ftp_calc = FtpCalculator.FtpCalculator()
            ftp_calc.add_activity_data(self.activity_type, self.start_time, self.bests)
            estimated_ftp = ftp_calc.estimate()
            if estimated_ftp:
                results[Keys.THRESHOLD_POWER] = estimated_ftp

        return results
