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
