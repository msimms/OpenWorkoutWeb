# Copyright 2019 Michael J Simms
"""Estimates VO2Max."""

class VO2MaxCalculator(object):
    """Estimates VO2Max"""

    def __init__(self):
        super(VO2MaxCalculator, self).__init__()

    def estimate_vo2max(self, max_hr, resting_hr):
        return 15.3 * (max_hr / resting_hr)
