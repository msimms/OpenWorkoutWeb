# Copyright 2020 Michael J Simms
"""Dscribes a rest day."""

import Workout

class Rest(Workout.Workout):
    """Class that describes a rest day."""

    def __init__(self, user_id):
        Workout.Workout.__init__(self, user_id)
