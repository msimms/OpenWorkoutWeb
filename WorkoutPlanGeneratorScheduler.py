# Copyright 2019 Michael J Simms
"""Schedules computationally expensive workout plan generation tasks"""

import sys
import traceback

from bson.json_util import dumps
from WorkoutPlanGenerator import generate_workout_plan

import Keys

class WorkoutPlanGeneratorScheduler(object):
    """Class for scheduling computationally expensive workout plan generation tasks."""

    def __init__(self):
        super(WorkoutPlanGeneratorScheduler, self).__init__()

    def add_to_queue(self, user_id, data_mgr):
        """Adds the user to the list of workout plans to be generated."""
        user_obj = {}
        user_obj[Keys.WORKOUT_PLAN_USER_ID_KEY] = user_id
        plan_task = generate_workout_plan.delay(dumps(user_obj))
        try:
            if data_mgr is not None:
                data_mgr.track_workout_plan_task(user_id, plan_task.task_id)
        except:
            print(traceback.format_exc())
            print(sys.exc_info()[0])
