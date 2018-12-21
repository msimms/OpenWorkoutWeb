# Copyright 2018 Michael J Simms
"""Writes GPX and TCX files."""

import DataMgr
import Keys
import GpxFileWriter
import TcxFileWriter

class Exporter(object):
    """Exporter for GPX and TCX location files."""

    def __init__(self):
        super(Exporter, self).__init__()

    def export_as_csv(self, file_name, activity):
        """Creates a CSV file for accelerometer data."""
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

    def nearest_sensor_reading(self, time_ms, current_reading, sensor_iter):
        try:
            while current_reading.keys()[0] < time_ms:
                current_reading = sensor_iter.next()
        except StopIteration:
            return None
        return current_reading

    def export_as_gpx(self, file_name, activity):
        """Creates a GPX file."""
        try:
            locations = []
            cadence_readings = []
            temp_readings = []
            power_readings = []

            if Keys.APP_LOCATIONS_KEY in activity:
                locations = activity[Keys.APP_LOCATIONS_KEY]
            if Keys.APP_CADENCE_KEY in activity:
                cadence_readings = activity[Keys.APP_CADENCE_KEY]
            if Keys.APP_TEMP_KEY in activity:
                temp_readings = activity[Keys.APP_TEMP_KEY]
            if Keys.APP_POWER_KEY in activity:
                power_readings = activity[Keys.APP_POWER_KEY]

            location_iter = iter(locations)
            cadence_iter = iter(cadence_readings)
            temp_iter = iter(temp_readings)
            power_iter = iter(power_readings)

            nearest_cadence = cadence_iter.next()
            nearest_temp = temp_iter.next()
            nearest_power = power_iter.next()

            with open(file_name, 'wt') as local_file:
                while True:
                    current_location = location_iter.next()
                    nearest_cadence = self.nearest_sensor_reading(current_location[Keys.LOCATION_TIME_KEY], nearest_cadence, cadence_iter)
                    nearest_temp = self.nearest_sensor_reading(current_location[Keys.LOCATION_TIME_KEY], nearest_temp, temp_iter)
                    nearest_power = self.nearest_sensor_reading(current_location[Keys.LOCATION_TIME_KEY], nearest_power, power_iter)
        except StopIteration:
            pass
        return True

    def export_as_tcx(self, file_name, activity):
        """Creates a TCX file."""
        try:
            locations = []
            cadence_readings = []
            temp_readings = []
            power_readings = []

            if Keys.APP_LOCATIONS_KEY in activity:
                locations = activity[Keys.APP_LOCATIONS_KEY]
            if Keys.APP_CADENCE_KEY in activity:
                cadence_readings = activity[Keys.APP_CADENCE_KEY]
            if Keys.APP_TEMP_KEY in activity:
                temp_readings = activity[Keys.APP_TEMP_KEY]
            if Keys.APP_POWER_KEY in activity:
                power_readings = activity[Keys.APP_POWER_KEY]

            location_iter = iter(locations)
            cadence_iter = iter(cadence_readings)
            temp_iter = iter(temp_readings)
            power_iter = iter(power_readings)

            nearest_cadence = cadence_iter.next()
            nearest_temp = temp_iter.next()
            nearest_power = power_iter.next()

            writer = TcxFileWriter.TcxFileWriter()
            if writer.create_file(file_name):
                if writer.start_activity(activity[Keys.ACTIVITY_TYPE_KEY]):
                    while True:
                        current_location = location_iter.next()
                        nearest_cadence = self.nearest_sensor_reading(current_location[Keys.LOCATION_TIME_KEY], nearest_cadence, cadence_iter)
                        nearest_temp = self.nearest_sensor_reading(current_location[Keys.LOCATION_TIME_KEY], nearest_temp, temp_iter)
                        nearest_power = self.nearest_sensor_reading(current_location[Keys.LOCATION_TIME_KEY], nearest_power, power_iter)
        except StopIteration:
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
