# Copyright 2018 Michael J Simms
"""Writes GPX and TCX files."""

import DataMgr
import Keys

class Exporter(object):
    """Exporter for GPX and TCX location files."""

    def __init__(self):
        super(Exporter, self).__init__()

    def export_as_cxv(self, file_name, activity):
        with open(file_name, 'wt') as local_file:
            pass
        return True

    def export_as_gpx(self, file_name, activity):
        with open(file_name, 'wt') as local_file:
            pass
        return True

    def export_as_tcx(self, file_name, activity):
        with open(file_name, 'wt') as local_file:
            pass
        return True

    def export(self, data_mgr, activity_id, file_name, file_type):
        activity = data_mgr.retrieve_activity(activity_id)
        if file_type == 'csv':
            return export_as_csv(file_name, activity)
        elif file_type == 'gpx':
            return export_as_gpx(file_name, activity)
        elif file_type == 'tcx':
            return export_as_tcx(file_name, activity)
        return False
