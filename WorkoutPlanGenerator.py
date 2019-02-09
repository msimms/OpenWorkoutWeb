# Copyright 2019 Michael J Simms
"""Handles the generation of a workout plan. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import logging
import os
import sys
import traceback
import DataMgr
import Keys

class WorkoutPlanGenerator(object):
    """Class for performing the computationally expensive workout plan generation tasks."""

    def __init__(self, user_obj):
        self.user_obj = user_obj
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr(root_dir, None, None, None)
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

    def generate_plan(self):
        """Main plan generation routine."""

        # Sanity check.
        if self.user_obj is None:
            return

        try:
            user_id = self.user_obj[Keys.RECORDS_USER_ID]
            self.data_mgr.retrieve_each_user_activity(self, user_id, WorkoutPlanGenerator.update_summary_data_cb)
            cycling_bests, running_bests = self.data_mgr.compute_recent_bests(user_id)
            if running_bests is not None:
                print running_bests
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error("Exception when generating a workout plan.")
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
