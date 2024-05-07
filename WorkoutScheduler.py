# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Michael J Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Organizes workouts."""

import copy
import datetime
import inspect
import os
import random
import sys
import Config
import InputChecker
import Keys
import UserMgr

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
        self.user_mgr = UserMgr.UserMgr(config=Config.Config(), session_mgr=None)

    def score_schedule(self, week):
        """Computes a score for the schedule, based on the daily stress scores."""
        """A better schedule is one with a more even distribution of stress."""
        """Lower is better."""

        # Compute the average daily stress.
        daily_stress_scores = [0.0] * 7
        index = 0
        for day in week:
            for workout in day:
                if workout.estimated_intensity_score is not None:
                    daily_stress_scores[index] = workout.estimated_intensity_score
            index = index + 1

        smoothed_scores = signals.smooth(daily_stress_scores, 2)
        avg_smoothed_scores = sum(smoothed_scores) / len(smoothed_scores)
        stdev_smoothed_scores = statistics.stddev(smoothed_scores, avg_smoothed_scores)
        return stdev_smoothed_scores

    def list_schedulable_days(self, unscheduleable_days, week):
        """Utility function for listing the days of the week for which no workout is currently schedule."""
        possible_days = []

        # Walk the weeks list and find a list of possible days on which to do the workout.
        day_index = 0
        for day in week:
            if len(day) == 0 and day_index not in unscheduleable_days:
                possible_days.append(day_index)
            day_index = day_index + 1
        return possible_days

    def deterministic_scheduler(self, workouts, week, unscheduleable_days, start_time):
        """Simple deterministic algorithm for scheduling workouts."""

        scheduled_workouts = copy.deepcopy(workouts)
        scheduled_week = copy.deepcopy(week)

        for workout in scheduled_workouts:

            # If this workout is not currently scheduled.
            if workout.scheduled_time is None:

                # Walk the weeks list and find a list of possible days on which to do the workout.
                possible_days = self.list_schedulable_days(unscheduleable_days, scheduled_week)

                # Pick one of the days from the candidate list.
                # If all the days are booked, then pick a random day.
                if len(possible_days) > 0:
                    day_index = possible_days[int(len(possible_days) / 2)]
                else:
                    day_index = random.randint(0,6)
                workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                scheduled_week[day_index].append(workout)

        return scheduled_workouts, scheduled_week

    def random_scheduler(self, workouts, week, start_time):
        """Randomly assigns workouts to days."""

        scheduled_workouts = copy.deepcopy(workouts)
        scheduled_week = copy.deepcopy(week)

        for workout in scheduled_workouts:

            # If this workout is not currently scheduled.
            if workout.scheduled_time is None:

                # Pick a random day.
                day_index = random.randint(0,6)
                workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                scheduled_week[day_index].append(workout)

        return scheduled_workouts, scheduled_week

    def schedule_workouts(self, workouts, start_time):
        """Organizes the workouts into a schedule for the next week. Implements a very basic constraint solving algorithm."""

        # Shuffle the deck.
        random.shuffle(workouts)

        # This will serve as our calendar for next week.
        week = [[] for _ in range(7)]

        # Do not schedule anything on these days.
        unscheduleable_days = []

        # Are there any events this week? If so, add them to the schedule first.
        for workout in workouts:
            if workout.type == Keys.WORKOUT_TYPE_EVENT:
                day_index = (workout.scheduled_time.timetuple().tm_wday + 1) % 7
                week[day_index].append(workout)
                unscheduleable_days.append(day_index)

        # When does the user want to do their long run?
        # Long runs should be the next priority after events.
        if self.user_id is not None:

            preferred_long_run_day = self.user_mgr.retrieve_user_setting(self.user_id, Keys.PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY)
            if preferred_long_run_day is not None:

                for workout in workouts:

                    # Long runs have a user defined constraint.
                    if workout.type == Keys.WORKOUT_TYPE_LONG_RUN:

                        # Convert the day name to an index and ignore case.
                        try:
                            day_index = [x.lower() for x in InputChecker.days_of_week].index(preferred_long_run_day)
                        except:
                            day_index = InputChecker.days_of_week[-1] # Default to the last day, Sunday.

                        # Make sure there isn't something else already on that date (such as an event).
                        if len(week[day_index]) == 0:
                            workout.scheduled_time = start_time + datetime.timedelta(days=day_index)
                            week[day_index].append(workout)
                            unscheduleable_days.append(day_index)
                        break

        # Assign workouts to days. Keep track of the one with the best score.
        # Start with a simple deterministic algorithm and then try to beat it.
        best_schedule, new_week = self.deterministic_scheduler(workouts, week, unscheduleable_days, start_time)
        best_schedule_score = self.score_schedule(new_week)

        # Try and best the first arrangement, by randomly re-arranging the schedule
        # and seeing if we can get a better score.
        #for _ in range(1, 10):
        #    new_schedule, new_week = self.random_scheduler(workouts, week, start_time)
        #    new_schedule_score = self.score_schedule(new_week)
        #    if new_schedule_score < best_schedule_score:
        #        best_schedule = new_schedule
        #        best_schedule_score = new_schedule_score

        return best_schedule
