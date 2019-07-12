# Copyright 2018 Michael J Simms
"""Defines the celery worker for activity analysis, activity import, and workout plan generation."""

from __future__ import absolute_import
import celery
celery_worker = celery.Celery('straen_worker', include=['ActivityAnalyzer', 'ImportWorker', 'WorkoutPlanGenerator'])
celery_worker.config_from_object('CeleryConfig')
