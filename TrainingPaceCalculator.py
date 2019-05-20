# Copyright 2019 Michael J Simms
"""Computes training paces based on previous efforts."""

import Keys
import VO2MaxCalculator

class TrainingPaceCalculator(object):
    """Computes training paces based on previous efforts"""

    def __init__(self):
        super(TrainingPaceCalculator, self).__init__()

    def convert_to_speed(self, vo2):
    	return 29.54 + 5.000663 * vo2 - 0.007546 * vo2 * vo2

    def calc_from_vo2max(self, vo2max):
        """Give the athlete's VO2Max, returns the suggested long run, easy run, tempo run, and speed run paces."""
        long_run_pace = vo2max * 0.6
        easy_pace = vo2max * 0.7
        tempo_pace = vo2max * 0.88
        speed_pace = vo2max * 1.1
        long_run_pace = self.convert_to_speed(long_run_pace)
        easy_pace = self.convert_to_speed(easy_pace)
        tempo_pace = self.convert_to_speed(tempo_pace)
        speed_pace = self.convert_to_speed(speed_pace)
        return [long_run_pace, easy_pace, tempo_pace, speed_pace]

    def calc_from_hr(self, max_hr, resting_hr):
        """Give the athlete's maximum and resting heart rates, returns the suggested long run, easy run, tempo run, and speed run paces."""
        v02maxCalc = VO2MaxCalculator()
        vo2max = v02maxCalc.estimate_vo2max_from_heart_rate(max_hr, resting_hr)
        return self.calc_from_vo2max(v02max)

    def calc_from_race_distance_in_meters(self, race_distance_meters, race_time_minutes):
        """Give the an athlete's recent race result, returns the suggested long run, easy run, tempo run, and speed run paces."""
        v02maxCalc = VO2MaxCalculator()
        vo2max = v02maxCalc.estimate_vo2max_from_race_distance_in_meters(race_distance_meters, race_time_minutes)
        return self.calc_from_vo2max(v02max)
