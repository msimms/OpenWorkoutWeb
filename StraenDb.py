# Copyright 2017 Michael J Simms
"""Database implementation"""

import sys
import traceback
from bson.objectid import ObjectId
import pymongo
import Database


class Device(object):
    def __init__(self):
        self.id = 0
        self.name = ""
        self.description = ""
        super(Device, self).__init__()


class MongoDatabase(Database.Database):
    conn = None
    database = None
    users_collection = None
    activities_collection = None

    def __init__(self, rootDir):
        Database.Database.__init__(self, rootDir)

    def connect(self):
        """Connects/creates the database"""
        try:
            self.conn = pymongo.MongoClient('localhost:27017')
            self.database = self.conn['straendb']
            self.users_collection = self.database['users']
            self.activities_collection = self.database['activities']
            return True
        except pymongo.errors.ConnectionFailure, e:
            self.log_error("Could not connect to MongoDB: %s" % e)
        return False

    def create_user(self, username, realname, passhash):
        """Create method for a user."""
        if username is None:
            self.log_error(MongoDatabase.create_user.__name__ + "Unexpected empty object: username")
            return False
        if realname is None:
            self.log_error(MongoDatabase.create_user.__name__ + "Unexpected empty object: realname")
            return False
        if passhash is None:
            self.log_error(MongoDatabase.create_user.__name__ + "Unexpected empty object: passhash")
            return False
        if len(username) == 0:
            self.log_error(MongoDatabase.create_user.__name__ + "username too short")
            return False
        if len(realname) == 0:
            self.log_error(MongoDatabase.create_user.__name__ + "realname too short")
            return False
        if len(passhash) == 0:
            self.log_error(MongoDatabase.create_user.__name__ + "hash too short")
            return False

        try:
            post = {"username": username, "realname": realname, "hash": passhash, "devices": [], "following": [], "followed by": []}
            self.users_collection.insert(post)
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_user(self, username):
        """Retrieve method for a user."""
        if username is None:
            self.log_error(MongoDatabase.retrieve_user.__name__ + "Unexpected empty object: username")
            return None, None, None
        if len(username) == 0:
            self.log_error(MongoDatabase.retrieve_user.__name__ + "username is empty")
            return None, None, None

        try:
            user = self.users_collection.find_one({"username": username})
            if user is not None:
                return str(user['_id']), user['hash'], user['realname']
            return None, None, None
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None, None, None

    def retrieve_matched_users(self, username):
        """Returns a list of user names for users that match the specified regex."""
        user_list = []

        if username is None:
            self.log_error(MongoDatabase.retrieve_matched_users.__name__ + "Unexpected empty object: username")
            return user_list
        if len(username) == 0:
            self.log_error(MongoDatabase.retrieve_matched_users.__name__ + "username is empty")
            return user_list

        try:
            matched_users = self.users_collection.find({"username": {"$regex": username}})
            if matched_users is not None:
                for matched_user in matched_users:
                    user_list.append(matched_user["username"])
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return user_list

    def create_user_device(self, user_id, device_str):
        """Create method for a device."""
        if user_id is None:
            self.log_error(MongoDatabase.create_user_device.__name__ + "Unexpected empty object: user_id")
            return False
        if device_str is None:
            self.log_error(MongoDatabase.create_user_device.__name__ + "Unexpected empty object: device_str")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id_obj})
            devices = []
            if user is not None:
                if 'devices' in user:
                    devices = user['devices']
            devices.append(device_str)
            user['devices'] = devices
            self.users_collection.save(user)
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return True

    def retrieve_user_devices(self, user_id):
        """Retrieve method for a device."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_user_devices.__name__ + "Unexpected empty object: user_id")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id_obj})
            if user is not None:
                if 'devices' in user:
                    return user['devices']
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_users_followed(self, user_id):
        """Returns the user ids for all users that are followed by the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_users_followed.__name__ + "Unexpected empty object: user_id")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id_obj})
            if user is not None:
                if 'following' in user:
                    return user['following']
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_followers(self, user_id):
        """Returns the user ids for all users that follow the user with the specified id."""
        if user_id is None:
            self.log_error(MongoDatabase.retrieve_followers.__name__ + "Unexpected empty object: user_id")
            return None

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id_obj})
            if user is not None:
                if 'followers' in user:
                    return user['followers']
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_following_entry(self, user_id, following_name):
        if user_id is None:
            self.log_error(MongoDatabase.create_following_entry.__name__ + "Unexpected empty object: user_id")
            return None
        if following_name is None:
            self.log_error(MongoDatabase.create_following_entry.__name__ + "Unexpected empty object: following_name")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id_obj})
            if user is not None:
                user_list = []
                if 'following' in user:
                    user_list = user['following']
                if following_name not in user_list:
                    user_list.append(following_name)
                    user['following'] = user_list
                    self.users_collection.save(user)
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_follower_entry(self, user_id, follower_name):
        if user_id is None:
            self.log_error(MongoDatabase.create_follower_entry.__name__ + "Unexpected empty object: user_id")
            return None
        if follower_name is None:
            self.log_error(MongoDatabase.create_follower_entry.__name__ + "Unexpected empty object: follower_name")
            return False

        try:
            user_id_obj = ObjectId(user_id)
            user = self.users_collection.find_one({"_id": user_id_obj})
            if user is not None:
                user_list = []
                if 'follower' in user:
                    user_list = user['follower']
                if follower_name not in user_list:
                    user_list.append(follower_name)
                    user['follower'] = user_list
                    self.users_collection.save(user)
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_device_activities(self, device_str, start, num_results):
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_device_activities.__name__ + "Unexpected empty object: device_str")
            return None

        try:
            return list(self.activities_collection.find({"device_str": device_str}).sort("_id", -1).skip(start).limit(num_results))
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_most_recent_activity_id_for_device(self, device_str):
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_most_recent_activity_id_for_device.__name__ + "Unexpected empty object: device_str")
            return None

        try:
            device_activities = self.activities_collection.find({"device_str": device_str}).sort("_id", -1).limit(1)
            if device_activities is not None and device_activities.count() > 0:
                activity = device_activities.next()
                return activity["activity_id"]
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_activity(self, activity_id, activty_name, device_str):
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: activity_id")
            return False
        if activty_name is None:
            self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: activty_name")
            return False
        if device_str is None:
            self.log_error(MongoDatabase.create_activity.__name__ + "Unexpected empty object: device_str")
            return False

        try:
            post = {"activity_id": str(activity_id), "activty_name": activty_name, "device_str": device_str, "visibility": "public", "locations": []}
            self.activities_collection.insert(post)
            return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_activity_visibility(self, device_str, activity_id):
        """Returns the visibility setting for the specified activity."""
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_activity_visibility.__name__ + "Unexpected empty object: device_str")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_activity_visibility.__name__ + "Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if activity is not None:
                if "visibility" in activity:
                    visibility = activity["visibility"]
                    return visibility
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def update_activity_visibility(self, device_str, activity_id, visibility):
        """Changes the visibility setting for the specified activity."""
        if device_str is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + "Unexpected empty object: device_str")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + "Unexpected empty object: activity_id")
            return None
        if visibility is None:
            self.log_error(MongoDatabase.update_activity_visibility.__name__ + "Unexpected empty object: visibility")
            return None

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if activity is not None:
                activity["visibility"] = visibility
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_activity_comment(self, device_str, activity_id, commenter_id, comment):
        """Create method for a comment on an activity."""
        if device_str is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + "Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + "Unexpected empty object: activity_id")
            return False
        if commenter_id is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + "Unexpected empty object: commenter_id")
            return False
        if comment is None:
            self.log_error(MongoDatabase.create_activity_comment.__name__ + "Unexpected empty object: comment")
            return False

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if len(activity) > 0:
                data = activity["comments"]
                data.append({commenter_id, comment})
                activity["comments"] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_metadata(self, device_str, activity_id, date_time, key, value):
        """Create method for a piece of metaadata."""
        if device_str is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: activity_id")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: date_time")
            return False
        if key is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: key")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_metadata.__name__ + "Unexpected empty object: value")
            return False

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if len(activity) == 0:
                if self.create_activity(activity_id, "", device_str):
                    activity = self.activities_collection.find_one({"device_id": device_str, "activity_id": str(activity_id)})
            if len(activity) > 0:
                data = []
                if key in activity:
                    data = activity[key]
                value = {str(date_time): str(value)}
                data.append(value)
                activity[key] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_metadata(self, key, device_str, activity_id):
        """Returns all the metadata for the specified sensor for the given activity."""
        if key is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + "Unexpected empty object: key")
            return None
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + "Unexpected empty object: device_str")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_metadata.__name__ + "Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if activity is not None:
                if key in activity:
                    metadata = activity[key]
                    if isinstance(metadata, list):
                        return metadata
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_sensordata(self, device_str, activity_id, date_time, sensor_type, value):
        """Create method for a piece of sensor data, such as a heart rate or power meter reading."""
        if device_str is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: activity_id")
            return False
        if date_time is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: date_time")
            return False
        if sensor_type is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: sensor_type")
            return False
        if value is None:
            self.log_error(MongoDatabase.create_sensordata.__name__ + "Unexpected empty object: value")
            return False

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if len(activity) == 0:
                if self.create_activity(activity_id, "", device_str):
                    activity = self.activities_collection.find_one({"device_id": device_str, "activity_id": str(activity_id)})
            if len(activity) > 0:
                data = []
                if sensor_type in activity:
                    data = activity[sensor_type]
                value = {str(date_time): str(value)}
                data.append(value)
                activity[sensor_type] = data
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def retrieve_sensordata(self, sensor_type, device_str, activity_id):
        """Returns all the sensor data for the specified sensor for the given activity."""
        if sensor_type is None:
            self.log_error(MongoDatabase.retrieve_sensordata.__name__ + "Unexpected empty object: sensor_type")
            return None
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_sensordata.__name__ + "Unexpected empty object: device_str")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_sensordata.__name__ + "Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if activity is not None:
                if sensor_type in activity:
                    sensor_data = activity[sensor_type]
                    return sensor_data
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def create_location(self, device_str, activity_id, date_time, latitude, longitude, altitude):
        """Create method for a location."""
        if device_str is None:
            self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: device_str")
            return False
        if activity_id is None:
            self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: activity_id")
            return False
        if latitude is None:
            self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: latitude")
            return False
        if longitude is None:
            self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: longitude")
            return False
        if altitude is None:
            self.log_error(MongoDatabase.create_location.__name__ + "Unexpected empty object: altitude")
            return False

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if activity is None:
                if self.create_activity(activity_id, "", device_str):
                    activity = self.activities_collection.find_one({"device_id": device_str, "activity_id": str(activity_id)})
            if activity is not None:
                location_list = []
                if 'locations' in activity:
                    location_list = activity['locations']
                value = {"time": date_time, "latitude": latitude, "longitude": longitude, "altitude": altitude}
                location_list.append(value)
                activity['locations'] = location_list
                self.activities_collection.save(activity)
                return True
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return False

    def create_sensor_reading(self, device_str, activity_id, date_time, key, value):
        """Inherited from LocationWriter. Processes a sensor reading from the importer."""
        pass

    def retrieve_locations(self, device_str, activity_id):
        """Returns all the locations for the specified activity."""
        if device_str is None:
            self.log_error(MongoDatabase.retrieve_locations.__name__ + "Unexpected empty object: device_str")
            return None
        if activity_id is None:
            self.log_error(MongoDatabase.retrieve_locations.__name__ + "Unexpected empty object: activity_id")
            return None

        try:
            activity = self.activities_collection.find_one({"activity_id": str(activity_id), "device_str": device_str})
            if activity is not None:
                locations = activity['locations']
                return locations
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None

    def retrieve_most_recent_locations(self, device_str, activity_id, num):
        """Returns the most recent 'num' locations for the specified activity."""
        if num is None:
            self.log_error(MongoDatabase.retrieve_most_recent_locations.__name__ + "Unexpected empty object: num")
            return None

        try:
            locations = self.retrieve_locations(device_str, activity_id)
            return locations
        except:
            traceback.print_exc(file=sys.stdout)
            self.log_error(sys.exc_info()[0])
        return None
