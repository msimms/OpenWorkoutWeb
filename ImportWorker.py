# Copyright 2019 Michael J Simms
"""Performs the computationally expensive import tasks. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import celery
import json
import logging
import os
import traceback
import uuid
import DataMgr
import Importer

def log_error(self, log_str):
    """Writes an error message to the log file."""
    print(log_str)
    logger = logging.getLogger()
    if logger is not None:
        logger.debug(log_str)

@celery_worker.task(track_started=True)
def import_activity(import_str):
    local_file_name = ""

    try:
        import_obj = json.loads(import_str)
        username = import_obj['username']
        user_id = import_obj['user_id']
        uploaded_file_data = import_obj['uploaded_file_data']
        uploaded_file_name = import_obj['uploaded_file_name']

        # Generate a random name for the local file.
        root_dir = os.path.dirname(os.path.abspath(__file__))
        tempfile_dir = os.path.join(root_dir, 'tempfile')
        if not os.path.exists(tempfile_dir):
            os.makedirs(tempfile_dir)
        upload_path = os.path.normpath(tempfile_dir)
        uploaded_file_name, uploaded_file_ext = os.path.splitext(uploaded_file_name)
        local_file_name = os.path.join(upload_path, str(uuid.uuid4()))
        local_file_name = local_file_name + uploaded_file_ext

        # Write the file.
        with open(local_file_name, 'wb') as local_file:
            local_file.write(uploaded_file_data)
            
        data_mgr = DataMgr.DataMgr("", root_dir, None, None, None)
        importer = Importer.Importer(data_mgr)
        importer.import_file(username, user_id, local_file_name, uploaded_file_name, uploaded_file_ext)
    except:
        log_error("Exception when importing activity data: " + str(import_str))
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    finally:
        # Remove the local file.
        if len(local_file_name) > 0:
            os.remove(local_file_name)

def main():
    """Entry point for an import worker."""
    pass

if __name__ == "__main__":
    main()
