# Copyright 2019 Michael J Simms
"""Computes estimated finishing times for running races, based on VO2 estimation."""

import math
import Keys

class RunningRacePredictor(object):
    """Computes estimated finishing times for running races, based on VO2 estimation."""

    def __init__(self):
        super(RunningRacePredictor, self).__init__()

    def calc_from_vo2max(self, vo2max):
        """Give the athlete's VO2Max, returns the estimated race completion times as a dictionary."""
        speed = 98.0581 * math.sqrt(vo2max + 84.4509) - 876.24
