# Copyright 2020 Michael J Simms
"""Dscribes a rest day."""

import Workout

class Event(Workout.Workout):
    """Class that describes a goal event."""

    def __init__(self, user_id):
        Event.Event.__init__(self, user_id)
