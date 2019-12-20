# Copyright 2019 Michael J Simms
"""Generates a run plan for the specifiied user."""

import Keys
import TrainingPaceCalculator
import Workout

class RunPlanGenerator(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id

    def is_workout_plan_possible(self, goal_distance, inputs):
        """Returns TRUE if we can actually generate a plan with the given contraints."""
        return True

    def gen_workouts_for_next_week(self, goal_distance, inputs):
        """Generates the workouts for the next week, but doesn't schedule them."""

        # 3 Critical runs: Speed session, tempo run, and long run
        # Long run: 10%/week increase for an experienced runner
        # Taper: 2 weeks for a marathon or more, 1 week for a half marathon or less

        speed_run_pace = inputs[Keys.SPEED_RUN_PACE]
        tempo_run_pace = inputs[Keys.TEMPO_RUN_PACE]
        long_run_pace = inputs[Keys.LONG_RUN_PACE]
        easy_run_pace = inputs[Keys.EASY_RUN_PACE]
        longest_run_in_four_weeks = inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY]

        # Handle situation in which the user hasn't run in four weeks
        if longest_run_in_four_weeks is None:
            raise Exception("No runs in the last four weeks.")

        # Handle situation in which the user is already meeting or exceeding the goal distance.


        # No pace data?
        if speed_run_pace is None or tempo_run_pace is None or long_run_pace is None or easy_run_pace is None:
            raise Exception("No run pace data.")

        workouts = []

        # Speed session. Start with four intervals, increase the number of intervals as we get closer to the goal.
        speed_run_workout = Workout.Workout(self.user_id)
        speed_run_workout.description = "Speed Run"
        speed_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        speed_run_workout.add_warmup(10 * 60)
        speed_run_workout.add_interval(3, longest_run_in_four_weeks / 10, speed_run_pace, 200, easy_run_pace)
        speed_run_workout.add_cooldown(5 * 60)
        workouts.append(speed_run_workout)

        # Tempo run
        tempo_run_workout = Workout.Workout(self.user_id)
        tempo_run_workout.description = "Tempo Run"
        tempo_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        tempo_run_workout.add_warmup(5 * 60)
        tempo_run_workout.add_interval(1, longest_run_in_four_weeks / 4, tempo_run_pace, 0, 0)
        tempo_run_workout.add_cooldown(5 * 60)
        workouts.append(tempo_run_workout)

        # Long run
        long_run_workout = Workout.Workout(self.user_id)
        long_run_workout.description = "Long Run"
        long_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        long_run_workout.add_interval(1, longest_run_in_four_weeks * 1.1, long_run_pace, 0, 0)
        workouts.append(long_run_workout)

        return workouts
