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
USERNAME_KEY = "username" # Login name for a user
PASSWORD_KEY = "password" # User's password
PASSWORD1_KEY = "password1" # User's password when creating an account
PASSWORD2_KEY = "password2" # User's confirmation password when creating an account
DEVICE_KEY = "device" # Unique identifier for the device which is recording the activity
DEVICES_KEY = "devices" # List of device identifiers
REALNAME_KEY = "realname" # User's real name
HASH_KEY = "hash" # Password hash
FRIEND_REQUESTS_KEY = "friend_requests"
FRIENDS_KEY = "friends"
REQUESTING_USER_KEY = "requesting_user"
PR_KEY = "pr" # Personal record
EMAIL_KEY = "email" # User's email
TARGET_EMAIL_KEY = "target_email" # Email address of another user

# User settings
DEFAULT_PRIVACY = "default privacy"
PREFERRED_UNITS_KEY = "preferred units"
UNITS_METRIC_KEY = "metric"
UNITS_STANDARD_KEY = "standard"
BIRTHDAY_KEY = "birthday"
DEFAULT_BIRTHDAY = "315532800"
HEIGHT_KEY = "height"
DEFAULT_HEIGHT = "1.8"
WEIGHT_KEY = "weight" # User's weight (kilograms)
DEFAULT_WEIGHT = "70"
GENDER_KEY = "gender"
GENDER_MALE_KEY = "male"
GENDER_FEMALE_KEY = "female"
RESTING_HEART_RATE_KEY = "resting heart rate"
ESTIMATED_MAX_HEART_RATE_KEY = "estimated max heart rate"
ESTIMATED_FTP_KEY = "estimated ftp"
PREFERRED_LONG_RUN_DAY_KEY = "preferred long run day" # Day of the week on which the user prefers to do their long runs
GOAL_TYPE_KEY = "goal type" # Extra info about the user's goal, such as whether they care about speed or just finishing a race
GOAL_TYPE_COMPLETION = "Completion"
GOAL_TYPE_SPEED = "Speed"

# Personal records
RECORDS_USER_ID = "user_id"
RECORD_NAME_KEY = "record_name"
PERSONAL_RECORDS = "records"

# Workout plans
WORKOUT_PLAN_USER_ID_KEY = "user_id"
WORKOUT_PLAN_CALENDAR_ID_KEY = "calendar id"
WORKOUT_LIST_KEY = "workouts"
WORKOUT_ID_KEY = "workout_id"
WORKOUT_TYPE_KEY = "type"
WORKOUT_DESCRIPTION_KEY = "description"
WORKOUT_SPORT_TYPE_KEY = "sport type"
WORKOUT_WARMUP_KEY = "warmup"
WORKOUT_INTERVALS_KEY = "intervals"
WORKOUT_COOLDOWN_KEY = "cooldown"
WORKOUT_SCHEDULED_TIME_KEY = "scheduled time"

# Workout types
WORKOUT_TYPE_REST = "Rest"
WORKOUT_TYPE_EVENT = "Event"
WORKOUT_TYPE_SPEED_RUN = "Speed Run"
WORKOUT_TYPE_INTERVAL_SESSION = "Interval Session"
WORKOUT_TYPE_TEMPO_RUN = "Tempo Run"
WORKOUT_TYPE_EASY_RUN = "Easy Run"
WORKOUT_TYPE_HILL_REPEATS = "Hill Repeats" # 4-10 repeats, depending on skill level, done at 5K pace
WORKOUT_TYPE_MIDDLE_DISTANCE_RUN = "Middle Distance Run" # 2 hour run for advanced distance runners
WORKOUT_TYPE_LONG_RUN = "Long Run"
WORKOUT_TYPE_OPEN_WATER_SWIM = "Open Water Swim"
WORKOUT_TYPE_POOL_WATER_SWIM = "Pool Swim"

# Keys associated with uploading data
UPLOADED_FILE_NAME_KEY = "uploaded_file_name"
UPLOADED_FILE_DATA_KEY = "uploaded_file_data"

# Keys inherited from the mobile app. Some of these are also used by the web app.
APP_NAME_KEY = "Name"
APP_TIME_KEY = "Time"
APP_USERNAME_KEY = "User Name"
APP_DEVICE_ID_KEY = "DeviceId"
APP_ID_KEY = "ActivityId"
APP_TYPE_KEY = "ActivityType"
APP_DISTANCE_KEY = "Distance"
APP_DURATION_KEY = "Duration"
APP_CADENCE_KEY = "Cadence" # Raw cadence list.
APP_TEMP_KEY = "Temperature"
APP_CURRENT_SPEED_KEY = "Current Speed"
APP_AVG_SPEED_KEY = "Avgerage Speed"
APP_MOVING_SPEED_KEY = "Moving Speed" 
APP_SPEED_VARIANCE_KEY = "Speed Variance"
APP_HEART_RATE_KEY = "Heart Rate"  # Raw heart rate list.
APP_AVG_HEART_RATE_KEY = "Average Heart Rate" # Computed average heart rate.
APP_CURRENT_PACE_KEY = "Current Pace" # Computed pace list.
APP_POWER_KEY = "Power" # Raw power data list.
APP_SETS_KEY = "Sets"
APP_DISTANCES_KEY = "distances" # Distance between data points.
APP_LOCATIONS_KEY = "locations" # Raw position data.
APP_LOCATION_LAT_KEY = "Latitude"
APP_LOCATION_LON_KEY = "Longitude"
APP_LOCATION_ALT_KEY = "Altitude"
APP_ACCELEROMETER_KEY = "accelerometer" # Raw accelerometer list.
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
ACTIVITY_ID_KEY = "activity_id" # Unique identifier for the activity
ACTIVITY_HASH_KEY = "activity_hash"
ACTIVITY_TYPE_KEY = "activity_type"
ACTIVITY_DESCRIPTION_KEY = "description"
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
ACTIVITY_COMMENTER_ID_KEY = "commenter_id" # User ID of the user leaving the comment on an activity
ACTIVITY_TAG_KEY = "tag"
ACTIVITY_TAGS_KEY = "tags"
ACTIVITY_SUMMARY_KEY = "summary_data"
ACTIVITY_EXPORT_FORMAT_KEY = "export_format"
ACTIVITY_NUM_POINTS = "num_points" 
ACTIVITY_LOCATION_DESCRIPTION_KEY = "location_description" # Political description of the activity location (i.e., Florida)
ACTIVITY_INTERVALS = "intervals" # Intervals that were computed from the workout

# Keys used to summarize activity data.
BEST_SPEED = "Best Speed"
BEST_PACE = "Best Pace"
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
AVG_PACE = "Average Pace"
AVG_POWER = "Average Power"
AVG_HEART_RATE = "Average Heart Rate"
AVG_CADENCE = "Average Cadence"
NORMALIZED_POWER = "Normalized Power"
THRESHOLD_POWER = "Threshold Power"
INTENSITY_FACTOR = "Intensity Factor"
TSS = "TSS" # Training Stress Score
RTSS = "rTSS" # Run Training Stress Score
VARIABILITY_INDEX = "Variability Index"
CLUSTER = "Cluster"
TOTAL_DISTANCE = "Total Distance"
LONGEST_DISTANCE = "Longest Distance"
MILE_SPLITS = "Mile Splits"
KM_SPLITS = "KM Splits"

# API-only keys.
SECONDS = "seconds"
DEVICE_LAST_HEARD_FROM = "last_heard_from"

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
GEAR_SERVICE_HISTORY = "service_history"

# Service record keys.
SERVICE_RECORD_ID_KEY = "service_id"
SERVICE_RECORD_DATE_KEY = "date"
SERVICE_RECORD_DESCRIPTION_KEY = "description"

# Activity types
TYPE_UNSPECIFIED_ACTIVITY = "Unknown"
TYPE_RUNNING_KEY = "Running"
TYPE_VIRTUAL_RUNNING_KEY = "Virtual Running"
TYPE_INDOOR_RUNNING_KEY = "Indoor Running"
TYPE_HIKING_KEY = "Hiking"
TYPE_WALKING_KEY = "Walking"
TYPE_CYCLING_KEY = "Cycling"
TYPE_INDOOR_CYCLING_KEY = "Indoor Cycling"
TYPE_VIRTUAL_CYCLING_KEY = "Virtual Cycling"
TYPE_MOUNTAIN_BIKING_KEY = "Mountain Biking"
TYPE_OPEN_WATER_SWIMMING_KEY = "Open Water Swimming"
TYPE_POOL_SWIMMING_KEY = "Pool Swimming"
TYPE_PULL_UP_KEY = "Pull Up"
TYPE_PUSH_UP_KEY = "Push Up"
FOOT_BASED_ACTIVITIES = [ TYPE_RUNNING_KEY, TYPE_INDOOR_RUNNING_KEY, TYPE_VIRTUAL_RUNNING_KEY, TYPE_HIKING_KEY, TYPE_WALKING_KEY ]
BIKE_BASED_ACTIVITIES = [ TYPE_CYCLING_KEY, TYPE_INDOOR_CYCLING_KEY, TYPE_VIRTUAL_CYCLING_KEY, TYPE_MOUNTAIN_BIKING_KEY ]
SWIMMING_ACTIVITIES = [ TYPE_OPEN_WATER_SWIMMING_KEY, TYPE_POOL_SWIMMING_KEY ]

# Activity names
UNNAMED_ACTIVITY_TITLE = "Unnamed"

# Interval workouts
INTERVAL_REPEAT_KEY = "Repeat"
INTERVAL_DISTANCE_KEY = "Distance"
INTERVAL_PACE_KEY = "Pace"
INTERVAL_RECOVERY_DISTANCE_KEY = "Recovery Distance"
INTERVAL_RECOVERY_PACE_KEY = "Recovery Pace"

# Goals
GOAL_KEY = "goal"
GOAL_DATE_KEY = "goal_date"
GOAL_SWIM_DISTANCE_KEY = "goal_swim_distance"
GOAL_BIKE_DISTANCE_KEY = "goal_bike_distance"
GOAL_RUN_DISTANCE_KEY = "goal_run_distance"
GOAL_FITNESS_KEY = "Fitness"
GOAL_5K_RUN_KEY = "5K Run"
GOAL_10K_RUN_KEY = "10K Run"
GOAL_15K_RUN_KEY = "15K Run"
GOAL_HALF_MARATHON_RUN_KEY = "Half Marathon"
GOAL_MARATHON_RUN_KEY = "Marathon"

# Used by the workout plan generator
LONGEST_RUN_IN_FOUR_WEEKS_KEY = "Longest Run In Four Weeks"
AGE_YEARS_KEY = "Age In Years"
EXPERIENCE_LEVEL_KEY = "Experience Level"
WEEKS_UNTIL_GOAL_KEY = "Weeks Until Goal"

# Used to track deferred tasks
DEFERRED_TASKS_USER_ID = "user_id"
TASKS_KEY = "tasks"
TASK_ID_KEY = "task id"
TASK_TYPE_KEY = "task type"
TASK_DETAILS_KEY = "task details"
TASK_STATUS_KEY = "task status"
IMPORT_TASK_KEY = "import"
ANALYSIS_TASK_KEY = "analysis"
WORKOUT_PLAN_TASK_KEY = "workout plan"
TASK_STATUS_QUEUED = "Queued"
TASK_STATUS_STARTED = "Started"
TASK_STATUS_FINISHED = "Finished"

# Things associated with deferred tasks
LOCAL_FILE_NAME = "local file name"

TIME_KEYS = [ BEST_1K, BEST_MILE, BEST_5K, BEST_10K, BEST_15K, BEST_HALF_MARATHON, BEST_MARATHON, BEST_METRIC_CENTURY, BEST_CENTURY ]
DISTANCE_KEYS = [ TOTAL_DISTANCE, LONGEST_DISTANCE ]
SPEED_KEYS = [ APP_CURRENT_SPEED_KEY, APP_AVG_SPEED_KEY, APP_MOVING_SPEED_KEY, APP_SPEED_VARIANCE_KEY, BEST_SPEED, APP_AVG_SPEED_KEY ]
PACE_KEYS = [ APP_CURRENT_PACE_KEY, BEST_PACE, AVG_PACE, LONG_RUN_PACE, EASY_RUN_PACE, TEMPO_RUN_PACE, SPEED_RUN_PACE, INTERVAL_PACE_KEY ]
POWER_KEYS = [ AVG_POWER, MAX_POWER, BEST_5_SEC_POWER, BEST_12_MIN_POWER, BEST_20_MIN_POWER, BEST_1_HOUR_POWER, NORMALIZED_POWER, THRESHOLD_POWER ]
HEART_RATE_KEYS = [ AVG_HEART_RATE, MAX_HEART_RATE ]
CADENCE_KEYS = [ APP_CADENCE_KEY, AVG_CADENCE, MAX_CADENCE ]
GOALS = [ GOAL_FITNESS_KEY, GOAL_5K_RUN_KEY, GOAL_10K_RUN_KEY, GOAL_15K_RUN_KEY, GOAL_HALF_MARATHON_RUN_KEY, GOAL_MARATHON_RUN_KEY ]

UNSUMMARIZABLE_KEYS = [ APP_SPEED_VARIANCE_KEY, APP_DISTANCES_KEY, APP_LOCATIONS_KEY, ACTIVITY_TIME_KEY, ACTIVITY_TYPE_KEY, ACTIVITY_HASH_KEY, ACTIVITY_LOCATION_DESCRIPTION_KEY, ACTIVITY_INTERVALS, MILE_SPLITS, KM_SPLITS ]
