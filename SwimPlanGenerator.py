# Copyright 2019 Michael J Simms
"""Generates a swim plan for the specifiied user."""

import Keys
import WorkoutFactory

class SwimPlanGenerator(object):
    """Class for generating a swim plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def is_workout_plan_possible(self, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    def gen_aerobic_swim(self):
        """Utility function for creating an aerobic-focused swim workout."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_POOL_SWIM, self.user_id)
        workout.sport_type = Keys.TYPE_POOL_SWIMMING_KEY

        return workout

    def gen_technique_swim(self):
        """Utility function for creating a technique swim workout."""

        # Create the workout object.
        workout = WorkoutFactory.create(Keys.WORKOUT_TYPE_TECHNIQUE_SWIM, self.user_id)
        workout.sport_type = Keys.TYPE_POOL_SWIMMING_KEY

        return workout
        
    def gen_workouts_for_next_week(self, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # Add critical workouts:

        # Technique swim.
        workouts.append(self.gen_technique_swim())

        return workouts
