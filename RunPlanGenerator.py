# Copyright 2019 Michael J Simms

import TrainingPaceCalculator
import Workout

class RunPlanGenerator(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def is_workout_plan_possible(self, goal_distance, weeks_until_goal):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    def gen_workouts_for_next_week(self, goal_distance, weeks_until_goal, longest_run_in_four_weeks, speed_run_pace, tempo_run_pace, long_run_pace):
        """Generates the workouts for the next week, but doesn't schedule them."""

        workouts = []

        # Speed session. Start with four intervals, increase the number of intervals as we get closer to the goal.
        speed_run_workout = Workout.Workout(self.user_id)
        speed_run_workout.description = "Speed Run"
        long_run_workout.intervals = [3, longest_run_in_four_weeks / 10, speed_run_pace]
        workouts.append(speed_run_workout)

        # Tempo run
        tempo_run_workout = Workout.Workout(self.user_id)
        tempo_run_workout.description = "Tempo Run"
        long_run_workout.intervals = [3, longest_run_in_four_weeks / 5, tempo_run_pace]
        workouts.append(tempo_run_workout)

        # Long run
        long_run_workout = Workout.Workout(self.user_id)
        long_run_workout.description = "Long Run"
        long_run_workout.intervals = [1, longest_run_in_four_weeks * 1.1, long_run_pace]
        workouts.append(long_run_workout)

        return workouts
