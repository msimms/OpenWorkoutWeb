# Copyright 2019 Michael J Simms

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
        longest_run_in_four_weeks = inputs[Keys.LONGEST_RUN_IN_FOUR_WEEKS_KEY]

        workouts = []

        # Speed session. Start with four intervals, increase the number of intervals as we get closer to the goal.
        speed_run_workout = Workout.Workout(self.user_id)
        speed_run_workout.description = "Speed Run"
        speed_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        interval = {}
        interval[Keys.INTERVAL_REPEAT_KEY] = 3
        interval[Keys.INTERVAL_DISTANCE_KEY] = longest_run_in_four_weeks / 10
        interval[Keys.INTERVAL_PACE_KEY] = speed_run_pace
        speed_run_workout.intervals.append(interval)
        workouts.append(speed_run_workout)

        # Tempo run
        tempo_run_workout = Workout.Workout(self.user_id)
        tempo_run_workout.description = "Tempo Run"
        tempo_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        interval = {}
        interval[Keys.INTERVAL_REPEAT_KEY] = 1
        interval[Keys.INTERVAL_DISTANCE_KEY] = longest_run_in_four_weeks / 5
        interval[Keys.INTERVAL_PACE_KEY] = tempo_run_pace
        tempo_run_workout.intervals.append(interval)
        workouts.append(tempo_run_workout)

        # Long run
        long_run_workout = Workout.Workout(self.user_id)
        long_run_workout.description = "Long Run"
        long_run_workout.sport_type = Keys.TYPE_RUNNING_KEY
        interval = {}
        interval[Keys.INTERVAL_REPEAT_KEY] = 1
        interval[Keys.INTERVAL_DISTANCE_KEY] = longest_run_in_four_weeks * 1.1
        interval[Keys.INTERVAL_PACE_KEY] = long_run_pace
        workouts.append(long_run_workout)

        return workouts
