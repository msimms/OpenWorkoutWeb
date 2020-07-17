# Copyright 2019 Michael J Simms
"""Computes the hash of an activity. Used to determine uniqueness."""

import hashlib
import sys
import Keys
import SensorAnalyzerFactory

class ActivityHasher(object):
    """Computes the hash of an activity. Used to determine uniqueness."""

    def __init__(self, activity):
        self.activity = activity
        super(ActivityHasher, self).__init__()

    def float_to_str(self, num):
        formatted_str = "{:.6f}".format(num)
        return formatted_str.encode('utf-8')

    def str_num_to_str(self, str_num):
        formatted_str = str(int(float(str_num)))
        return formatted_str

    def hash(self):
        """Main analysis routine."""

        # Sanity check.
        if self.activity is None:
            return

        # We're going to hash the activity so we'll know if it's been modified.
        h = hashlib.sha512()

        # Hash the locations.
        print("Hashing locations...")
        if Keys.ACTIVITY_LOCATIONS_KEY in self.activity:
            locations = self.activity[Keys.ACTIVITY_LOCATIONS_KEY]
            for location in locations:
                date_time = str(int(location[Keys.LOCATION_TIME_KEY])).encode('utf-8')
                latitude = self.float_to_str(location[Keys.LOCATION_LAT_KEY])
                longitude = self.float_to_str(location[Keys.LOCATION_LON_KEY])
                altitude = self.float_to_str(location[Keys.LOCATION_ALT_KEY])

                h.update(date_time)
                h.update(latitude)
                h.update(longitude)
                h.update(altitude)

        # Hash the sensor data. The order in which we hash sensor data needs to match the order in the mobile app.
        print("Hashing sensor data...")
        sensor_types_to_analyze = [Keys.APP_ACCELEROMETER_KEY, Keys.APP_HEART_RATE_KEY, Keys.APP_POWER_KEY]
        for sensor_type in sensor_types_to_analyze:
            if sensor_type in self.activity:
                print("Hashing " + sensor_type + " data...")

                # Accelerometer data is stored differently....
                if sensor_type == Keys.APP_ACCELEROMETER_KEY:
                    for datum in self.activity[sensor_type]:
                        time = str(datum[Keys.ACCELEROMETER_TIME_KEY]).encode('utf-8')
                        x = self.float_to_str(datum[Keys.ACCELEROMETER_AXIS_NAME_X])
                        y = self.float_to_str(datum[Keys.ACCELEROMETER_AXIS_NAME_Y])
                        z = self.float_to_str(datum[Keys.ACCELEROMETER_AXIS_NAME_Z])

                        h.update(time)
                        h.update(x)
                        h.update(y)
                        h.update(z)
                else:
                    for datum in self.activity[sensor_type]:
                        if sys.version_info[0] < 3:
                            time = self.str_num_to_str(datum.keys()[0])
                            value = self.str_num_to_str(datum.values()[0])
                        else:
                            time = self.str_num_to_str(list(datum.keys())[0]).encode('utf-8')
                            value = self.str_num_to_str(list(datum.values())[0]).encode('utf-8')

                        h.update(time)
                        h.update(value)

        # Finalize the hash digest.
        hash_str = h.hexdigest()
        return hash_str
