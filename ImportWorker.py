# Copyright 2019 Michael J Simms
"""Schedules computationally expensive import tasks"""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import os
import DataMgr
import Importer

@celery_worker.task(track_started=True)
def import_activity(import_str):
    try:
        import_obj = json.loads(import_str)

        username = import_obj['username']
        user_id = import_obj['user_id']
        local_file_name = import_obj['local_file_name']
        uploaded_file_name = import_obj['uploaded_file_name']
        file_extension = import_obj['file_extension']

        data_mgr = DataMgr.DataMgr(os.path.dirname(os.path.abspath(__file__)), None, None)
        importer = Importer.Importer(data_mgr)
        importer.import_file(username, user_id, local_file_name, uploaded_file_name, file_extension)
    finally:
        # Remove the local file.
        os.remove(local_file_name)

def main():
    """Entry point for an import worker."""
    pass

if __name__ == "__main__":
    main()
