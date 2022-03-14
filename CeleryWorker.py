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
import datetime
import random

import AnalysisScheduler
import DataMgr
import Keys
import UserMgr
import Units
import WorkoutPlanGeneratorScheduler

celery_worker = celery.Celery('straen_worker', include=['ActivityAnalyzer', 'ImportWorker', 'WorkoutPlanGenerator'])
celery_worker.config_from_object('CeleryConfig')

@celery_worker.task()
def check_for_unanalyzed_activities():
    """Check for activities that need to be analyzed. Do one, if any are found."""
    analysis_scheduler = AnalysisScheduler.AnalysisScheduler()
    data_mgr = DataMgr.DataMgr(None, "", analysis_scheduler, None, None)
    unanalyzed_activity_list = data_mgr.retrieve_unanalyzed_activity_list(64)
    if len(unanalyzed_activity_list) > 0:
        activity_id = random.choice(unanalyzed_activity_list)
        data_mgr.analyze_activity_by_id(activity_id, None)

@celery_worker.task()
def check_for_ungenerated_workout_plans():
    """Checks for users that need their workout plan regenerated. Generates workout plans for each of those users."""
    now = datetime.datetime.utcnow()
    data_mgr = DataMgr.DataMgr(None, "", None, None, WorkoutPlanGeneratorScheduler.WorkoutPlanGeneratorScheduler())
    user_mgr = UserMgr.UserMgr(None)

    # These users don't have any pending workouts.
    user_ids = data_mgr.retrieve_users_without_scheduled_workouts()
    for user_id in user_ids:

        # Make sure we're not thrashing by only allowing workout generation once per day per user.
        last_gen_time = user_mgr.retrieve_user_setting(user_id, Keys.USER_PLAN_LAST_GENERATED_TIME)
        gen = (now - last_gen_time).total_seconds() > Units.SECS_PER_DAY
        if gen:
            data_mgr.generate_workout_plan_for_user(user_id)
            user_mgr.update_user_setting(user_id, Keys.USER_PLAN_LAST_GENERATED_TIME, now, now)

@celery_worker.task()
def prune_deferred_tasks_list():
    """Checks for users that need their workout plan regenerated."""
    data_mgr = DataMgr.DataMgr(None, "", None, None, None)
    data_mgr.prune_deferred_tasks_list()

@celery_worker.on_after_configure.connect
def setup_periodic_tasks(**kwargs):
    celery_worker.add_periodic_task(700.0, prune_deferred_tasks_list.s(), name='Removes completed tasks from the deferred tasks list.')
    celery_worker.add_periodic_task(600.0, check_for_ungenerated_workout_plans.s(), name='Check for workout plans that need to be re-generated.')
    celery_worker.add_periodic_task(500.0, check_for_unanalyzed_activities.s(), name='Check for activities that need to be analyzed. Do one, if any are found.')
