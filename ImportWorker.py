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
"""Performs the computationally expensive import tasks. Implements a celery worker."""

from __future__ import absolute_import
from CeleryWorker import celery_worker
import base64
import json
import logging
import os
import sys
import traceback
import uuid
import zlib
import Config
import DataMgr
import Importer
import Keys

def log_error(log_str):
    """Writes an error message to the log file."""
    print(log_str)
    logger = logging.getLogger()
    if logger is not None:
        logger.debug(log_str)

@celery_worker.task(ignore_result=True)
def import_activity(import_str, internal_task_id):
    local_file_name = ""

    try:
        import_obj = json.loads(import_str)
        username = import_obj['username']
        user_id = import_obj['user_id']
        uploaded_file_data = import_obj['uploaded_file_data']
        uploaded_file_name = import_obj['uploaded_file_name']
        desired_activity_id = import_obj['desired_activity_id']
        data_mgr = DataMgr.DataMgr(config=Config.Config(), root_url="", analysis_scheduler=None, import_scheduler=None, workout_plan_gen_scheduler=None)
        importer = Importer.Importer(data_mgr)

        # Generate a random name for the local file.
        print("Generating local file name...")
        root_dir = os.path.dirname(os.path.abspath(__file__))
        tempfile_dir = os.path.join(root_dir, 'tempfile')
        if not os.path.exists(tempfile_dir):
            os.makedirs(tempfile_dir)
        upload_path = os.path.normpath(tempfile_dir)
        uploaded_file_name, uploaded_file_ext = os.path.splitext(uploaded_file_name)
        local_file_name = os.path.join(upload_path, str(uuid.uuid4()))
        local_file_name = local_file_name + uploaded_file_ext

        # Decode and write the file.
        print("Writing the data to a local file...")
        with open(local_file_name, 'wb') as local_file:

            # Data to import is expected to be Base 64 encoded. This is because, at this point, we don't distinguish between
            # text and binary files.
            print("Base64 decoding...")
            uploaded_file_data = uploaded_file_data.replace(" ", "+") # Some JS base64 encoders replace plus with space, so we need to undo that.
            decoded_file_data = base64.b64decode(uploaded_file_data)
#            print("zlib decompressing...")
#            decoded_file_data = zlib.decompress(decoded_file_data)
            print("Writing...")
            local_file.write(decoded_file_data)

        # Update the status of the analysis in the database.
        print("Updating status...")
        data_mgr.update_deferred_task(user_id, internal_task_id, None, Keys.TASK_STATUS_STARTED)

        # Import the file into the database.
        print("Importing the data to the database...")
        success, _, activity_id = importer.import_activity_from_file(username, user_id, local_file_name, uploaded_file_name, uploaded_file_ext, desired_activity_id)

        # The import was successful, do more stuff.
        if success:

            # Save the file to the database.
            print("Saving the file to the database...")
            data_mgr.create_uploaded_file(activity_id, decoded_file_data)

            # Update the status of the analysis in the database.
            print("Updating status...")
            data_mgr.update_deferred_task(user_id, internal_task_id, activity_id, Keys.TASK_STATUS_FINISHED)

            # Schedule the activity for analysis.
            #print("Importing was successful, performing analysis...")
            #data_mgr.analyze_activity_by_id(activity_id, user_id)

        # The import failed.
        else:

            # Update the status of the analysis in the database.
            print("Import was not successful.")
            data_mgr.update_deferred_task(user_id, internal_task_id, activity_id, Keys.TASK_STATUS_ERROR)
    except:
        log_error("Exception when importing activity data: " + str(import_str))
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    finally:
        # Remove the local file.
        if len(local_file_name) > 0:
            print("Removing local file...")
            os.remove(local_file_name)

def main():
    """Entry point for an import worker."""
    pass

if __name__ == "__main__":
    main()
