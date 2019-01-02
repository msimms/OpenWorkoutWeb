# Copyright 2018 Michael J Simms
"""Defines the celery worker for activity analysis"""

from __future__ import absolute_import
import celery
celery_worker = celery.Celery('straen_worker', backend='rpc://', include=['ActivityAnalyzer'])
celery_worker.config_from_object('CeleryConfig')
