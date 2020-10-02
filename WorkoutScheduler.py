# Copyright 2019 Michael J Simms
"""Organizes workouts."""

import copy
import datetime
import inspect
import os
import random
import sys
import InputChecker
import Keys
import UserMgr
import WorkoutFactory

# Locate and load the peaks module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import signals
import statistics

class WorkoutScheduler(object):
    """Organizes workouts."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.user_mgr = UserMgr.UserMgr(None)

    def score_schedule(self, week):
        """Computes a score for the schedule, based on the daily stress scores."""
        """A better schedule is one with a more even distribution of stress."""
        """Lower is better."""

        # Compute the average daily stress.
        daily_stress_scores = [0.0] * 7
        index = 0
        for day in week:
            if day is not None:
                if day.estimated_training_stress is not None:
                    daily_stress_scores[index] = day.estimated_training_stress
            index = index + 1

        smoothed_scores = signals.smooth(daily_stress_scores, 2)
        avg_smoothed_scores = sum(smoothed_scores) / len(smoothed_scores)
        stdev_smoothed_scores = statistics.stddev(daily_stress_scores, avg_smoothed_scores)
        return stdev_smoothed_scores

    def list_schedulable_days(self, week):
        """Utility function for listing the days of the week for which no workout is currently schedule."""
        possible_days = []

        # Walk the weeks list and find a list of possible days on which to do the workout.
        day_index = 0
        for day in week:
            if day is None:
                possible_days.append(day_index)
            day_index = day_index + 1
        return possible_days

    def deterministic_scheduler(self, workouts, week, start_time):
        """Simple deterministic algorithm for scheduling workouts."""

        scheduled_workouts = copy.deepcopy(workouts)
        scheduled_week = copy.deepcopy(week)

        for workout in scheduled_workouts:

            # If this workout is not currently scheduled.
            if workout.scheduled_time is None:

                # Walk the weeks list and find a list of possible days on which to do the workout.
                possible_days = self.list_schedulable_days(scheduled_week)

                # Pick one of the days from the candidate list.
                if len(possible_days) > 0:
                    day_index = possible_days[int(len(possible_days) / 2)]
                    workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                    scheduled_week[day_index] = workout

        return scheduled_workouts, scheduled_week

    def random_scheduler(self, workouts, week, start_time):
        """Randomly assigns workouts to days."""

        scheduled_workouts = copy.deepcopy(workouts)
        scheduled_week = copy.deepcopy(week)

        for workout in scheduled_workouts:

            # If this workout is not currently scheduled.
            if workout.scheduled_time is None:

                # Walk the weeks list and find a list of possible days on which to do the workout.
                possible_days = self.list_schedulable_days(scheduled_week)

                # Pick one of the days from the candidate list.
                if len(possible_days) > 0:
                    day_index = random.choice(possible_days)
                    workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                    scheduled_week[day_index] = workout

        return scheduled_workouts, scheduled_week

    def schedule_workouts(self, workouts, start_time):
        """Organizes the workouts into a schedule for the next week. Implements a very basic constraint solving algorithm."""

        # This will server as our calendar for next week.
        week = [None] * 7

        # Find the long run and put it on the preferred day.
        if self.user_id is not None:

            # When does the user want to do long runs?
            preferred_long_run_day = self.user_mgr.retrieve_user_setting(self.user_id, Keys.PREFERRED_LONG_RUN_DAY_KEY)
            if preferred_long_run_day is not None:

                for workout in workouts:

                    # Long runs have a user defined constraint.
                    if workout.type == Keys.WORKOUT_TYPE_LONG_RUN:

                        # Convert the day name to an index and ignore case.
                        try:
                            day_index = [x.lower() for x in InputChecker.days_of_week].index(preferred_long_run_day)
                        except:
                            day_index = InputChecker.days_of_week[-1] # Default to the last day, Sunday.
                        workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                        week[day_index] = workout
                        break

        # Assign workouts to days. Keep track of the one with the best score.
        # Start with a simple deterministic algorithm and then try to beat it.
        best_schedule, best_week = self.deterministic_scheduler(workouts, week, start_time)
        best_schedule_score = self.score_schedule(best_week)

        # Try and best the first arrangement, by randomly re-arranging the schedule
        # and seeing if we can get a better score.
        for i in range(1, 10):
            new_schedule, new_week = self.random_scheduler(workouts, week, start_time)
            new_schedule_score = self.score_schedule(new_week)
            if new_schedule_score < best_schedule_score:
                best_schedule = new_schedule
                best_week = new_week
                best_schedule_score = new_schedule_score

        return best_schedule
