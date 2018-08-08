# Copyright 2018 Michael J Simms
"""Writes GPX and TCX files."""

import DataMgr
import StraenKeys

class Exporter(object):
    """Exporter for GPX and TCX location files."""

    def __init__(self):
        super(Exporter, self).__init__()

    def export(self, data_mgr, activity_id):
        data_mgr.retrieve_locations(activity_id)
        data_mgr.retrieve_metadata(key, activity_id)
        data_mgr.retrieve_sensordata(key, activity_id)

        return ""
