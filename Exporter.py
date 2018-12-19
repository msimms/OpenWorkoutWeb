# Copyright 2018 Michael J Simms
"""Writes GPX and TCX files."""

import DataMgr
import Keys

class Exporter(object):
    """Exporter for GPX and TCX location files."""

    def __init__(self):
        super(Exporter, self).__init__()

    def export_as_csv(self, file_name, activity):
        with open(file_name, 'wt') as local_file:
            if Keys.APP_ACCELEROMETER_KEY in activity:
                accel_readings = activity[Keys.APP_ACCELEROMETER_KEY]
                for reading in accel_readings:
                    accel_time = reading[Keys.ACCELEROMETER_TIME_KEY]
                    accel_x = reading[Keys.ACCELEROMETER_AXIS_NAME_X]
                    accel_y = reading[Keys.ACCELEROMETER_AXIS_NAME_Y]
                    accel_z = reading[Keys.ACCELEROMETER_AXIS_NAME_Z]
                    local_file.write(str(accel_time) + "," + str(accel_x) + "," + str(accel_y) + "," + str(accel_z) + "\n")
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
            return self.export_as_csv(file_name, activity)
        elif file_type == 'gpx':
            return self.export_as_gpx(file_name, activity)
        elif file_type == 'tcx':
            return self.export_as_tcx(file_name, activity)
        return False
