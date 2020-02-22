# Copyright 2019 Michael J Simms

import datetime
import os
import InputChecker
import Keys
import UserMgr

class WorkoutScheduler(object):
    """Class for generating a run plan for the specifiied user."""

    def __init__(self, user_id):
        self.user_id = user_id
        self.user_mgr = UserMgr.UserMgr(None)

    def schedule_workouts(self, workouts, start_time):
        """Organizes the workouts into a schedule for the next week. Implements a very basic constraint solving algorithm."""
        preferred_long_run_day = self.user_mgr.retrieve_user_setting(self.user_id, Keys.PREFERRED_LONG_RUN_DAY_KEY)

        # This will server as our calendar for next week.
        week = [None] * 7

        # Find the long run and put it on the preferred day.
        if preferred_long_run_day is not None:
            for workout in workouts:
                if workout.type == Keys.WORKOUT_TYPE_LONG_RUN:

                    # Convert the day name to an index and ignore case.
                    day_index = [x.lower() for x in InputChecker.days_of_week].index(preferred_long_run_day)
                    workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                    week[day_index] = workout
                    break

        # Assign workouts to days, while attempting to satisfy all constraints.
        for workout in workouts:

            if workout.scheduled_time is None:
                possible_days = []

                # Walk the weeks list and find a list of possible days on which to do the workout.
                day_index = 0
                for day in week:
                    if day is None:
                        possible_days.append(day_index)
                    day_index = day_index + 1

                # Pick one of the days from the candidate list.
                if len(possible_days) > 0:
                    day_index = possible_days[len(possible_days) / 2]
                    workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                    week[day_index] = workout

                    # Do we need to schedule a rest day after this workout?
                    if workout.needs_rest_day_afterwards:
                        pass

        return workouts
