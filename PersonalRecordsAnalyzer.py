# Copyright 2018 Michael J Simms
"""Handles computationally expensive analysis tasks. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import json
import DataMgr

@celery_worker.task(ignore_result=True)
def analyze_personal_records(user_id):
    print("Starting personal record analysis...")
    print(user_str)
    user_obj = json.loads(user_str)
    analyzer = ActivityAnalyzer(activity_obj, internal_task_id)
    data_mgr.refresh_personal_records_cache()
    print("Personal record analysis finished")

def main():
    """Entry point for an analysis worker."""
    pass

if __name__ == "__main__":
    main()
