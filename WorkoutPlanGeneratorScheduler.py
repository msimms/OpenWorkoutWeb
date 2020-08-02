# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Mike Simms
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
"""Schedules computationally expensive workout plan generation tasks"""

class WorkoutPlanGeneratorScheduler(object):
    """Class for scheduling computationally expensive workout plan generation tasks."""

    def __init__(self):
        super(WorkoutPlanGeneratorScheduler, self).__init__()

    def add_user_to_queue(self, user_id, data_mgr):
        """Adds the user to the list of workout plans to be generated."""
        from bson.json_util import dumps
        from WorkoutPlanGenerator import generate_workout_plan_for_user

        import Keys

        user_obj = {}
        user_obj[Keys.WORKOUT_PLAN_USER_ID_KEY] = user_id

        plan_task = generate_workout_plan_for_user.delay(dumps(user_obj))
        data_mgr.create_deferred_task(user_id, Keys.WORKOUT_PLAN_TASK_KEY, plan_task.task_id, None)

    def add_inputs_to_queue(self, inputs, data_mgr):
        """Adds the input data set to the list of workout plans to be generated."""
        from bson.json_util import dumps
        from WorkoutPlanGenerator import generate_workout_plan_from_inputs

        plan_task = generate_workout_plan_from_inputs.delay(dumps(user_obj))
        data_mgr.create_deferred_task(user_id, Keys.WORKOUT_PLAN_TASK_KEY, plan_task.task_id, None)
