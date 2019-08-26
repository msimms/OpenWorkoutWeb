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
"""Key strings for all key/value pairs used in the app"""

# Keys associated with user management.
SESSION_KEY = '_straen_username'
DATABASE_ID_KEY = "_id"
USERNAME_KEY = "username"
PASSWORD_KEY = "password"
PASSWORD1_KEY = "password1"
PASSWORD2_KEY = "password2"
DEVICE_KEY = "device"
REALNAME_KEY = "realname"
HASH_KEY = "hash"
DEVICES_KEY = "devices"
FOLLOWING_KEY = "following"
PR_KEY = "pr"
EMAIL_KEY = "email"
TARGET_EMAIL_KEY = "target_email"

# User settings
DEFAULT_PRIVACY = "default privacy"
PREFERRED_UNITS_KEY = "preferred units"
UNITS_METRIC_KEY = "metric"
UNITS_STANDARD_KEY = "standard"
BIRTHDAY_KEY = "birthday"
DEFAULT_BIRTHDAY = "315532800"
HEIGHT_KEY = "height"
DEFAULT_HEIGHT = "1.8"
WEIGHT_KEY = "weight"
DEFAULT_WEIGHT = "70"
GENDER_KEY = "gender"
GENDER_MALE_KEY = "male"
GENDER_FEMALE_KEY = "female"
RESTING_HEART_RATE_KEY = "resting heart rate"
ESTIMATED_MAX_HEART_RATE_KEY = "estimated max heart rate"
ESTIMATED_FTP_KEY = "estimated ftp"

# Personal records
RECORDS_USER_ID = "user_id"
RECORD_NAME = "record_name"
PERSONAL_RECORDS = "records"

# Workout plans
WORKOUT_PLAN_USER_ID = "user_id"

# Keys associated with uploading data
UPLOADED_FILE_NAME_KEY = "uploaded_file_name"
UPLOADED_FILE_DATA_KEY = "uploaded_file_data"

# Keys inherited from the mobile app.
APP_NAME_KEY = "Name"
APP_TIME_KEY = "Time"
APP_USERNAME_KEY = "User Name"
APP_DEVICE_ID_KEY = "DeviceId"
APP_ID_KEY = "ActivityId"
APP_TYPE_KEY = "ActivityType"
APP_DISTANCE_KEY = "Distance"
APP_DURATION_KEY = "Duration"
APP_CADENCE_KEY = "Cadence"
APP_TEMP_KEY = "Temperature"
APP_CURRENT_SPEED_KEY = "Current Speed"
APP_AVG_SPEED_KEY = "Avgerage Speed"
APP_MOVING_SPEED_KEY = "Moving Speed"
APP_SPEED_VARIANCE_KEY = "Speed Variance"
APP_HEART_RATE_KEY = "Heart Rate"
APP_AVG_HEART_RATE_KEY = "Average Heart Rate"
APP_CURRENT_PACE_KEY = "Current Pace"
APP_POWER_KEY = "Power"
APP_SETS_KEY = "Sets"
APP_LOCATIONS_KEY = "locations"
APP_LOCATION_LAT_KEY = "Latitude"
APP_LOCATION_LON_KEY = "Longitude"
APP_LOCATION_ALT_KEY = "Altitude"
APP_ACCELEROMETER_KEY = "accelerometer"
APP_AXIS_NAME_X = "x"
APP_AXIS_NAME_Y = "y"
APP_AXIS_NAME_Z = "z"

LOCATION_LAT_KEY = "latitude"
LOCATION_LON_KEY = "longitude"
LOCATION_ALT_KEY = "altitude"
LOCATION_TIME_KEY = "time"

ACCELEROMETER_AXIS_NAME_X = "x"
ACCELEROMETER_AXIS_NAME_Y = "y"
ACCELEROMETER_AXIS_NAME_Z = "z"
ACCELEROMETER_TIME_KEY = "time"

# Keys used exclusively by the web app.
ACTIVITY_ID_KEY = "activity_id"
ACTIVITY_HASH_KEY = "activity_hash"
ACTIVITY_TYPE_KEY = "activity_type"
ACTIVITY_USER_ID_KEY = "user_id"
ACTIVITY_DEVICE_STR_KEY = "device_str"
ACTIVITY_LOCATIONS_KEY = "locations"
ACTIVITY_NAME_KEY = "name"
ACTIVITY_TIME_KEY = "time"
ACTIVITY_END_TIME_KEY = "end_time"
ACTIVITY_VISIBILITY_KEY = "visibility"
ACTIVITY_VISIBILITY_PUBLIC = "public"
ACTIVITY_VISIBILITY_PRIVATE = "private"
ACTIVITY_COMMENT_KEY = "comment"
ACTIVITY_COMMENTS_KEY = "comments"
ACTIVITY_COMMENTER_ID_KEY = "commenter_id"
ACTIVITY_TAG_KEY = "tag"
ACTIVITY_TAGS_KEY = "tags"
ACTIVITY_SUMMARY_KEY = "summary_data"
ACTIVITY_EXPORT_FORMAT_KEY = "export_format"
ACTIVITY_NUM_POINTS = "num_points"

# Keys used to summarize activity data.
BEST_SPEED = "Best Speed"
BEST_1K = "Best 1K"
BEST_MILE = "Best Mile"
BEST_5K = "Best 5K"
BEST_10K = "Best 10K"
BEST_15K = "Best 15K"
BEST_HALF_MARATHON = "Best Half Marathon"
BEST_MARATHON = "Best Marathon"
BEST_METRIC_CENTURY = "Best Metric Century"
BEST_CENTURY = "Best Century"
BEST_5_SEC_POWER = "5 Second Power"
BEST_12_MIN_POWER = "12 Minute Power"
BEST_20_MIN_POWER = "20 Minute Power"
BEST_1_HOUR_POWER = "1 Hour Power"
MAX_POWER = "Maximum Power"
MAX_HEART_RATE = "Maximum Heart Rate"
MAX_CADENCE = "Maximum Cadence"
AVG_POWER = "Average Power"
AVG_HEART_RATE = "Average Heart Rate"
AVG_CADENCE = "Average Cadence"
NORMALIZED_POWER = "Normalized Power"
THRESHOLD_POWER = "Threshold Power"
INTENSITY_FACTOR = "Intensity Factor"
TSS = "TSS"
VARIABILITY_INDEX = "Variability Index"
CLUSTER = "Cluster"
TOTAL_DISTANCE = "Total Distance"
LONGEST_DISTANCE = "Longest Distance"

# Running paces.
LONG_RUN_PACE = "Long Run Pace"
EASY_RUN_PACE = "Easy Run Pace"
TEMPO_RUN_PACE = "Tempo Run Pace"
SPEED_RUN_PACE = "Speed Run Pace"

# Keys used to manage gear.
GEAR_KEY = "gear"
GEAR_ID_KEY = "gear_id"
GEAR_TYPE_KEY = "type"
GEAR_NAME_KEY = "name"
GEAR_DESCRIPTION_KEY = "description"
GEAR_ADD_TIME_KEY = "add_time"
GEAR_RETIRE_TIME_KEY = "retire_time"
GEAR_INITIAL_DISTANCE_KEY = "initial_distance"
GEAR_TYPE_BIKE = "bike"
GEAR_TYPE_SHOES = "shoes"

# Activity types
TYPE_UNSPECIFIED_ACTIVITY = "Unknown"
TYPE_RUNNING_KEY = "Running"
TYPE_HIKING_KEY = "Hiking"
TYPE_CYCLING_KEY = "Cycling"
TYPE_SWIMMING_KEY = "Swimming"
TYPE_PULL_UPS_KEY = "Pull Ups"
TYPE_PUSH_UPS_KEY = "Push Ups / Press Ups"

# Activity names
UNNAMED_ACTIVITY_TITLE = "Unnamed"

# Goals
GOAL_KEY = "goal"
GOAL_DATE_KEY = "goal_date"
GOAL_5K_RUN_KEY = "5K Run"
GOAL_10K_RUN_KEY = "10K Run"
GOAL_15K_RUN_KEY = "15K Run"
GOAL_HALF_MARATHON_RUN_KEY = "Half Marathon"
GOAL_MARATHON_RUN_KEY = "Marathon"

TIME_KEYS = [ BEST_1K, BEST_MILE, BEST_5K, BEST_10K, BEST_15K, BEST_HALF_MARATHON, BEST_MARATHON, BEST_METRIC_CENTURY, BEST_CENTURY ]
DISTANCE_KEYS = [ TOTAL_DISTANCE, LONGEST_DISTANCE ]
SPEED_KEYS = [ APP_CURRENT_SPEED_KEY, APP_AVG_SPEED_KEY, APP_MOVING_SPEED_KEY, APP_SPEED_VARIANCE_KEY, BEST_SPEED, APP_AVG_SPEED_KEY ]
PACE_KEYS = [ LONG_RUN_PACE, EASY_RUN_PACE, TEMPO_RUN_PACE, SPEED_RUN_PACE ]
POWER_KEYS = [ AVG_POWER, MAX_POWER, BEST_5_SEC_POWER, BEST_12_MIN_POWER, BEST_20_MIN_POWER, BEST_1_HOUR_POWER, NORMALIZED_POWER, THRESHOLD_POWER ]
HEART_RATE_KEYS = [ AVG_HEART_RATE, MAX_HEART_RATE ]
CADENCE_KEYS = [ AVG_CADENCE, MAX_CADENCE ]
GOALS = [ GOAL_5K_RUN_KEY, GOAL_10K_RUN_KEY, GOAL_15K_RUN_KEY, GOAL_HALF_MARATHON_RUN_KEY, GOAL_MARATHON_RUN_KEY ]

UNSUMMARIZABLE_KEYS = [ APP_SPEED_VARIANCE_KEY, ACTIVITY_TIME_KEY, ACTIVITY_TYPE_KEY, ACTIVITY_HASH_KEY]
