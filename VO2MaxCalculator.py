# Copyright 2019 Michael J Simms
"""Estimates VO2Max."""

class VO2MaxCalculator(object):
    """Estimates VO2Max"""

    def __init__(self):
        super(VO2MaxCalculator, self).__init__()

    def estimate_vo2max_from_heart_rate(self, max_hr, resting_hr):
        return 15.3 * (max_hr / resting_hr)

    def estimate_vo2max_from_race_distance_in_meters(self, race_distance_meters, race_time_minutes):
        speed = race_distance_meters / race_time_minutes
    	return -4.60 + 0.182258 * speed + 0.000104 * speed * speed
