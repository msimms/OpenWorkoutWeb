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

    def floatToStr(self, num):
        formatted_str = "{:.6f}".format(num)
        return formatted_str.encode('utf-8')

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
                latitude = self.floatToStr(location[Keys.LOCATION_LAT_KEY])
                longitude = self.floatToStr(location[Keys.LOCATION_LON_KEY])
                altitude = self.floatToStr(location[Keys.LOCATION_ALT_KEY])

                h.update(date_time)
                h.update(latitude)
                h.update(longitude)
                h.update(altitude)

        # Hash the sensor data.
        print("Hashing sensor data...")
        sensor_types_to_analyze = SensorAnalyzerFactory.supported_sensor_types()
        for sensor_type in sensor_types_to_analyze:
            if sensor_type in self.activity:
                print("Hashing " + sensor_type + " data...")
                for datum in self.activity[sensor_type]:
                    if sys.version_info[0] < 3:
                        time = str(int(datum.keys()[0]).encode('utf-8'))
                        value = self.floatToStr(datum.values()[0])
                    else:
                        time = str(int(list(datum.keys())[0]).encode('utf-8'))
                        value = self.floatToStr(list(datum.values())[0])

                    h.update(time)
                    h.update(value)

        # Finalize the hash digest.
        hash_str = h.hexdigest()
        return hash_str
