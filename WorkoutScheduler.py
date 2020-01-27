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
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_mgr = UserMgr.UserMgr(None, root_dir)

    def schedule_workouts(self, workouts):
        """Organizes the workouts into a schedule for the next week."""
        preferred_long_run_day = self.user_mgr.retrieve_user_setting(self.user_id, Keys.PREFERRED_LONG_RUN_DAY_KEY)

        # This will server as our calendar for next week.
        week = [None] * 7

        # What is the first day of next week?
        today = datetime.datetime.now().date()
        start = today + datetime.timedelta(days=7-today.weekday())

        # Find the long run and put it on the preferred day.
        if preferred_long_run_day is None:
            for workout in workouts:
                if self.description == Keys.WORKOUT_DESCRIPTION_LONG_RUN:
                    start_index = InputChecker.days_of_week.index(preferred_long_run_day)
                    long_run_time = start + datetime.timedelta(days=start_index)
                    workout.scheduled_time = long_run_time
                    week[start_index] = workout

        for workout in workouts:
            if workout.scheduled_time is None:
                pass

        return workouts
