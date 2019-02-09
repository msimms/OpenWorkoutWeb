# Copyright 2019 Michael J Simms
"""Handles the generation of a workout plan. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import logging
import os

class WorkoutPlanGenerator(object):
    """Class for performing the computationally expensive workout plan generation tasks."""

    def __init__(self, user):
        self.user = user
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_mgr = DataMgr.DataMgr(root_dir, None, None)
        super(WorkoutPlanGenerator, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        print(log_str)
        logger = logging.getLogger()
        if logger is not None:
            logger.debug(log_str)

@celery_worker.task()
def create_workout_plan(user_str):
    print("Starting workout plan generation...")
    user_obj = json.loads(user_str)
    print("Workout plan generation finished")

def main():
    """Entry point for a workout plan generator."""
    pass

if __name__ == "__main__":
    main()
