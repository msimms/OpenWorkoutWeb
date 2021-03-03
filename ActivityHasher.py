# Copyright 2019 Michael J Simms
"""Computes the hash of an activity. Used to determine uniqueness."""

import hashlib
import sys
import Keys

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

        # Finalize the hash digest.
        hash_str = h.hexdigest()
        return hash_str
