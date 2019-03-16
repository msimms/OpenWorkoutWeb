# Copyright 2019 Michael J Simms
"""Handles the generation of a workout plan. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import logging
import os
import sys
import time
import traceback
import AnalysisScheduler
import DataMgr
import UserMgr
import Keys

class WorkoutPlanGenerator(object):
    """Class for performing the computationally expensive workout plan generation tasks."""

    def __init__(self, user_obj):
        self.user_obj = user_obj
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr("", root_dir, AnalysisScheduler.AnalysisScheduler(), None, None)
        self.user_mgr = UserMgr.UserMgr(None, root_dir)
        super(WorkoutPlanGenerator, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        print(log_str)
        logger = logging.getLogger()
        if logger is not None:
            logger.debug(log_str)

    @staticmethod
    def update_summary_data_cb(context, activity, user_id):
        """Callback function for update_summary_data."""
        if Keys.ACTIVITY_SUMMARY_KEY not in activity:
            analysis_obj = context.data_mgr.analyze(activity, user_id)

    def calculate_inputs(self, user_id):
        """Looks through the user's data and calculates the neural net inputs."""

        now = time.time()
        tempo_pace = None   # Tempo pace is ~30 secs/mile slower than 5K race pace.
        longest_run = None  # Longest run in the last four weeks

        # Fetch the detail of the user's goal.
        goal = self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_KEY)
        goal_date = int(self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_DATE_KEY))
        if goal_date <= now:
            raise Exception("The goal date should be in the future.")
        weeks_until_goal = (goal_date - now) / (7 * 24 * 60 * 60) # Convert to weeks

        self.data_mgr.retrieve_each_user_activity(self, user_id, WorkoutPlanGenerator.update_summary_data_cb)

        # Look through the user's six month records.
        cycling_bests, running_bests = self.data_mgr.compute_recent_bests(user_id, DataMgr.SIX_MONTHS)
        if running_bests is not None:
            if Keys.BEST_5K in running_bests:
                best_5K = running_bests[Keys.BEST_5K][0]
                tempo_pace = (best_5K - (30.0 * 3.1)) / 5000.0 # Tempo pace per km
        if cycling_bests is not None:
            if Keys.THRESHOLD_POWER in cycling_bests:
                threshold_power = cycling_bests[Keys.THRESHOLD_POWER]
                best_recent_threshold_power = self.data_mgr.retrieve_user_estimated_ftp(user_id)
                if best_recent_threshold_power is None or threshold_power > best_recent_threshold_power:
                    self.data_mgr.store_user_estimated_ftp(user_id, threshold_power)

        # Look through the user's four week records.
        cycling_bests, running_bests = self.data_mgr.compute_recent_bests(user_id, DataMgr.FOUR_WEEKS)
        if running_bests is not None:
            if Keys.LONGEST_DISTANCE in running_bests:
                longest_run = running_bests[Keys.LONGEST_DISTANCE]

        # Compute the user's age in years.
        birthday = int(self.user_mgr.retrieve_user_setting(user_id, Keys.BIRTHDAY_KEY))
        age_years = (now - birthday) / (365.25 * 24 * 60 * 60)

        inputs = [ tempo_pace, longest_run, age_years, 0, goal, weeks_until_goal ]
        return inputs

    def generate_outputs(self, user_id, inputs):
        """Runs the neural network."""
        return []

    def organize_schedule(self, user_id, plan):
        """Arranges the user's workouts into days/weeks, etc."""
        pass

    def generate_plan(self):
        """Entry point for workout plan generation."""

        # Sanity check.
        if self.user_obj is None:
            self.log_error("User information not provided.")
            return

        try:
            user_id = self.user_obj[Keys.WORKOUT_PLAN_USER_ID]
            inputs = self.calculate_inputs(user_id)
            outputs = self.generate_outputs(user_id, inputs)
            self.organize_schedule(user_id, outputs)
        except:
            self.log_error("Exception when generating a workout plan.")
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])

@celery_worker.task()
def generate_workout_plan(user_str):
    print("Starting workout plan generation...")
    user_obj = json.loads(user_str)
    generator = WorkoutPlanGenerator(user_obj)
    generator.generate_plan()
    print("Workout plan generation finished")

def main():
    """Entry point for a workout plan generator."""
    pass

if __name__ == "__main__":
    main()
