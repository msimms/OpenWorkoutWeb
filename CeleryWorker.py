# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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
"""Defines the celery worker for activity analysis, activity import, and workout plan generation."""

from __future__ import absolute_import
import celery

import DataMgr
import WorkoutPlanGeneratorScheduler

celery_worker = celery.Celery('straen_worker', include=['ActivityAnalyzer', 'ImportWorker', 'WorkoutPlanGenerator'])
celery_worker.config_from_object('CeleryConfig')

@celery_worker.task()
def check_for_ungenerated_workout_plans():
    """Checks for users that need their workout plan regenerated."""
    data_mgr = DataMgr.DataMgr("", None, None, WorkoutPlanGeneratorScheduler.WorkoutPlanGeneratorScheduler())
    user_ids = data_mgr.retrieve_users_without_scheduled_workouts()
    for user_id in user_ids:
        data_mgr.generate_workout_plan(user_id)

@celery_worker.on_after_configure.connect
def setup_periodic_tasks(**kwargs):
    celery_worker.add_periodic_task(600.0, check_for_ungenerated_workout_plans.s(), name='Check for workout plans that need to be re-generated.')
