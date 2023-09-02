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
"""Key strings for all key/value pairs used in the app."""
"""Basically this contains all the string constants."""

# Keys associated with user management.
SESSION_KEY = "current_session_key"
DATABASE_ID_KEY = "_id"
USERNAME_KEY = "username" # Login name for a user
USER_ID_KEY = "user_id" # Unique identifier for a user
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
TIMESTAMP_KEY = "timestamp" # Some app messages have timestamps on them
API_KEYS = "api keys" # List of API keys belonging to the user
API_KEY = "key" # API key being provided
API_KEY_RATE = "rate" # The maximum number of requests allowed per day for the provided key

# Keys associated with session management.
SESSION_TOKEN_KEY = "cookie"
SESSION_USER_KEY = "user"
SESSION_EXPIRY_KEY = "expiry"

# Celery.
CELERY_PROJECT_NAME = "openworkoutweb_worker"

# Goals.
GOAL_FITNESS_KEY = "Fitness"
GOAL_5K_RUN_KEY = "5K Run"
GOAL_10K_RUN_KEY = "10K Run"
GOAL_15K_RUN_KEY = "15K Run"
GOAL_HALF_MARATHON_RUN_KEY = "Half Marathon"
GOAL_MARATHON_RUN_KEY = "Marathon"
GOAL_50K_RUN_KEY = "50K Run"
GOAL_50_MILE_RUN_KEY = "50 Mile Run"
GOAL_SPRINT_TRIATHLON_KEY = "Sprint Triathlon"
GOAL_OLYMPIC_TRIATHLON_KEY = "Olympic Triathlon"
GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY = "Half Iron Distance Triathlon"
GOAL_IRON_DISTANCE_TRIATHLON_KEY = "Iron Distance Triathlon"

# Goal types.
GOAL_TYPE_KEY = "goal type" # Extra info about the user's goal, such as whether they care about speed or just finishing a race
GOAL_TYPE_COMPLETION = "Completion"
GOAL_TYPE_SPEED = "Speed"

# Goal attributes used by the workout plan generator.
GOAL_SWIM_DISTANCE_KEY = "Goal Swim Distance"
GOAL_BIKE_DISTANCE_KEY = "Goal Bike Distance"
GOAL_RUN_DISTANCE_KEY = "Goal Run Distance"

# User settings that are exclusive to the workout plan generator.
PLAN_INPUT_GOAL_KEY = "Goal"
PLAN_INPUT_GOAL_DATE_KEY = "Goal Date" # Goal date in Unix time
PLAN_INPUT_LONGEST_RUN_WEEK_1_KEY = "Longest Run Week 1" # Most recent week
PLAN_INPUT_LONGEST_RUN_WEEK_2_KEY = "Longest Run Week 2" # Second most recent week
PLAN_INPUT_LONGEST_RUN_WEEK_3_KEY = "Longest Run Week 3" # Third most recent week
PLAN_INPUT_LONGEST_RUN_WEEK_4_KEY = "Longest Run Week 4" # Fourth most recent week
PLAN_INPUT_LONGEST_RIDE_WEEK_1_KEY = "Longest Ride Week 1" # Most recent week
PLAN_INPUT_LONGEST_RIDE_WEEK_2_KEY = "Longest Ride Week 2" # Second most recent week
PLAN_INPUT_LONGEST_RIDE_WEEK_3_KEY = "Longest Ride Week 3" # Third most recent week
PLAN_INPUT_LONGEST_RIDE_WEEK_4_KEY = "Longest Ride Week 4" # Fourth most recent week
PLAN_INPUT_LONGEST_SWIM_WEEK_1_KEY = "Longest Swim Week 1" # Most recent week
PLAN_INPUT_LONGEST_SWIM_WEEK_2_KEY = "Longest Swim Week 2" # Second most recent week
PLAN_INPUT_LONGEST_SWIM_WEEK_3_KEY = "Longest Swim Week 3" # Third most recent week
PLAN_INPUT_LONGEST_SWIM_WEEK_4_KEY = "Longest Swim Week 4" # Fourth most recent week
PLAN_INPUT_TOTAL_INTENSITY_WEEK_1_KEY = "Total Intensity Week 1" # Most recent week
PLAN_INPUT_TOTAL_INTENSITY_WEEK_2_KEY = "Total Intensity Week 2" # Second most recent week
PLAN_INPUT_TOTAL_INTENSITY_WEEK_3_KEY = "Total Intensity Week 3" # Third most recent week
PLAN_INPUT_TOTAL_INTENSITY_WEEK_4_KEY = "Total Intensity Week 4" # Fourth most recent week
PLAN_INPUT_AGE_YEARS_KEY = "Age In Years"
PLAN_INPUT_EXPERIENCE_LEVEL_KEY = "Experience Level" # Athlete's experience level with running (scale 1-10)
PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY = "Structured Training Comfort Level" # Athlete's comfort level (i.e. experience) with doing intervals, long runs, etc. (scale 1-10)
PLAN_INPUT_WEEKS_UNTIL_GOAL_KEY = "Weeks Until Goal"
PLAN_INPUT_AVG_RUNNING_DISTANCE_IN_FOUR_WEEKS = "Average Running Distance (Last 4 Weeks)"
PLAN_INPUT_AVG_CYCLING_DISTANCE_IN_FOUR_WEEKS = "Average Cycling Distance (Last 4 Weeks)"
PLAN_INPUT_AVG_CYCLING_DURATION_IN_FOUR_WEEKS = "Average Cycling Duration (Last 4 Weeks)"
PLAN_INPUT_AVG_SWIMMING_DISTANCE_IN_FOUR_WEEKS = "Average Swimming Distance (Last 4 Weeks)"
PLAN_INPUT_NUM_RUNS_LAST_FOUR_WEEKS = "Number of Runs (Last 4 Weeks)"
PLAN_INPUT_NUM_RIDES_LAST_FOUR_WEEKS = "Number of Rides (Last 4 Weeks)"
PLAN_INPUT_NUM_SWIMS_LAST_FOUR_WEEKS = "Number of Swims (Last 4 Weeks)"
PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY = "Preferred Long Run Day" # Day of the week on which the user prefers to do their long runs

# Unit systems.
UNITS_METRIC_KEY = "metric"
UNITS_STANDARD_KEY = "standard"

# Biological sexes.
BIOLOGICAL_MALE_KEY = "male" # Biological male
BIOLOGICAL_FEMALE_KEY = "female" # Biological female

# User settings.
REQUESTED_SETTING_KEY = "requested setting"
REQUESTED_SETTINGS_KEY = "requested settings" # For requesting a list of settings (more efficient than requesting settings one by one)
DEFAULT_PRIVACY_KEY = "default privacy"
USER_PREFERRED_UNITS_KEY = "preferred units" # The unit system preferred by the user, can be either UNITS_METRIC_KEY or UNITS_STANDARD_KEY
USER_PREFERRED_FIRST_DAY_OF_WEEK_KEY = "preferred first day of week" # Which day of the week does the user consider to be the first day of the week?
USER_BIRTHDAY_KEY = "birthday" # User's birthday
DEFAULT_BIRTHDAY_KEY = "315532800"
USER_HEIGHT_KEY = "height" # User's height (weight)
DEFAULT_HEIGHT_KEY = 1.8 # Default height (meters)
USER_WEIGHT_KEY = "weight" # User's weight (kilograms)
DEFAULT_WEIGHT_KEY = 70.0 # Default weight (kilograms)
USER_BIOLOGICAL_SEX_KEY = "biological sex" # The sex to use when computing calorie burn
USER_RESTING_HEART_RATE_KEY = "resting heart rate" # Resting heart rate, in bpm, specified by the user
USER_MAXIMUM_HEART_RATE_KEY = "max heart rate" # Maximum heart rate, in bpm, specified by the user
ESTIMATED_MAX_HEART_RATE_KEY = "estimated max heart rate" # Maximum heart rate, in bpm, computed from activities
ESTIMATED_MAX_HEART_RATE_LIST_KEY = "estimated max heart rate list" # List of all maximum heart rates, in bpm, computed from activities
BEST_CYCLING_20_MINUTE_POWER_LIST_KEY = "best 20 minute power list" # List of the best cycling 20 minute power values from each activity
ESTIMATED_CYCLING_FTP_KEY = "estimated ftp" # Estimated FTP, in watts
GEN_WORKOUTS_WHEN_RACE_CAL_IS_EMPTY = "gen workouts when race cal is empty" # If True we'll still run the workout plan generator even when the race calendar is empty
USER_CAN_UPLOAD_PHOTOS_KEY = "can upload photos" # User is allowed to upload photos
USER_IS_ADMIN_KEY = "is admin" # User is allowed to administer the site
USER_HAS_SWIMMING_POOL_ACCESS = "has swimming pool access" # Indicates whether or not the user has access to a swimming pool
USER_HAS_OPEN_WATER_SWIM_ACCESS = "has open water swim access" # Indicates whether or not the user can do open water swims
USER_HAS_BICYCLE = "has bicycle" # Indicates whether or not the user has access to a bicycle (or bike trainer)
USER_PLAN_LAST_GENERATED_TIME = "workout plan last generated" # Time of when a workout plan was last generated
USER_ACTIVITY_SUMMARY_CACHE_LAST_PRUNED = "activity summary cache last pruned" # Time at which we last cleaned up the activity summary cache
USER_RACES = "races" # List of races the user intends to do
ACTIVITY_HEAT_MAP = "heat map" # Dictionary mapping an activity location (i.e., Florida) to a count
USER_SETTINGS = [ DEFAULT_PRIVACY_KEY, USER_PREFERRED_UNITS_KEY, USER_PREFERRED_FIRST_DAY_OF_WEEK_KEY, USER_BIRTHDAY_KEY, USER_HEIGHT_KEY, USER_WEIGHT_KEY, \
    USER_BIOLOGICAL_SEX_KEY, USER_RESTING_HEART_RATE_KEY, USER_MAXIMUM_HEART_RATE_KEY, ESTIMATED_MAX_HEART_RATE_KEY, ESTIMATED_MAX_HEART_RATE_LIST_KEY, \
    BEST_CYCLING_20_MINUTE_POWER_LIST_KEY, ESTIMATED_CYCLING_FTP_KEY, GOAL_TYPE_KEY, PLAN_INPUT_EXPERIENCE_LEVEL_KEY, PLAN_INPUT_PREFERRED_LONG_RUN_DAY_KEY, \
    PLAN_INPUT_STRUCTURED_TRAINING_COMFORT_LEVEL_KEY, GEN_WORKOUTS_WHEN_RACE_CAL_IS_EMPTY, USER_CAN_UPLOAD_PHOTOS_KEY, USER_IS_ADMIN_KEY, \
    USER_HAS_SWIMMING_POOL_ACCESS, USER_HAS_OPEN_WATER_SWIM_ACCESS, USER_HAS_BICYCLE, USER_PLAN_LAST_GENERATED_TIME, USER_ACTIVITY_SUMMARY_CACHE_LAST_PRUNED, \
    USER_RACES, ACTIVITY_HEAT_MAP ]
USER_SETTINGS_LAST_UPDATED_KEY = "last updated" # Time when the user settings where last updated

# Personal records.
RECORD_NAME_KEY = "record_name"
PERSONAL_RECORDS_KEY = "records"

# Workout training intensity distribution.
TRAINING_PHILOSOPHY_POLARIZED = "polarized"
TRAINING_PHILOSOPHY_PYRAMIDAL = "pyramidal"
TRAINING_PHILOSOPHY_THRESHOLD = "threshold"

# Max Zone 1, Zone 2, and Zone 3 total intensity distributions for each training load philosophy.
# The buckets correspond to the amount of time spent in each lactate zone.
TID_THRESHOLD = [55, 55, 20]
TID_POLARIZED = [85, 10, 25]
TID_PYRAMIDAL = [75, 25, 10]

# Workout plans.
WORKOUT_PLAN_CALENDAR_ID_KEY = "calendar id"
WORKOUT_LIST_KEY = "workouts"
WORKOUT_ID_KEY = "workout_id"
WORKOUT_FORMAT_KEY = "format"
WORKOUT_TYPE_KEY = "workout type"
WORKOUT_DESCRIPTION_KEY = "description"
WORKOUT_ACTIVITY_TYPE_KEY = "activity type"
WORKOUT_WARMUP_KEY = "warmup"
WORKOUT_INTERVALS_KEY = "intervals"
WORKOUT_COOLDOWN_KEY = "cooldown"
WORKOUT_SCHEDULED_TIME_KEY = "scheduled time"
WORKOUT_LAST_SCHEDULED_WORKOUT_TIME_KEY = "last scheduled workout time"
WORKOUT_ESTIMATED_INTENSITY_KEY = "estimated intensity score"

# Workout types.
WORKOUT_TYPE_REST = "Rest"
WORKOUT_TYPE_EVENT = "Event"
WORKOUT_TYPE_SPEED_RUN = "Speed Session" # A run with speed intervals
WORKOUT_TYPE_THRESHOLD_RUN = "Threshold Run" # A run at threshold pace
WORKOUT_TYPE_TEMPO_RUN = "Tempo Run" # A run at tempo pace
WORKOUT_TYPE_EASY_RUN = "Easy Run" # A run at an easy pace
WORKOUT_TYPE_LONG_RUN = "Long Run" # Long run
WORKOUT_TYPE_FREE_RUN = "Free Run" # A run at no specific pace
WORKOUT_TYPE_HILL_REPEATS = "Hill Repeats" # 4-10 repeats, depending on skill level, done at 5K pace
WORKOUT_TYPE_PROGRESSION_RUN = "Progression Run" # A run with increasing pace
WORKOUT_TYPE_FARTLEK_RUN = "Fartlek Session" # A run in which the user can vary the pace at will
WORKOUT_TYPE_MIDDLE_DISTANCE_RUN = "Middle Distance Run" # 2 hour run for advanced distance runners
WORKOUT_TYPE_HILL_RIDE = "Hill Ride" # Hill workout on the bike
WORKOUT_TYPE_BIKE_CADENCE_DRILLS = "Cadence Drills" # Cadence drills on the bike
WORKOUT_TYPE_SPEED_INTERVAL_RIDE = "Speed Interval Ride" # A bike ride with speed intervals
WORKOUT_TYPE_TEMPO_RIDE = "Tempo Ride" # A bike ride at tempo pace/power
WORKOUT_TYPE_EASY_RIDE = "Easy Ride" # A bike ride at an easy pace/power
WORKOUT_TYPE_SWEET_SPOT_RIDE = "Sweet Spot Ride" # A bike ride with intervals just below threshold power
WORKOUT_TYPE_OPEN_WATER_SWIM = "Open Water Swimming"
WORKOUT_TYPE_POOL_SWIM = "Pool Swimming"
WORKOUT_TYPE_TECHNIQUE_SWIM = "Technique Swim"
RUN_WORKOUTS  = [ WORKOUT_TYPE_SPEED_RUN, WORKOUT_TYPE_THRESHOLD_RUN, WORKOUT_TYPE_TEMPO_RUN, WORKOUT_TYPE_EASY_RUN, \
                  WORKOUT_TYPE_LONG_RUN, WORKOUT_TYPE_FREE_RUN, WORKOUT_TYPE_HILL_REPEATS, WORKOUT_TYPE_PROGRESSION_RUN, \
                  WORKOUT_TYPE_FARTLEK_RUN, WORKOUT_TYPE_MIDDLE_DISTANCE_RUN ]
BIKE_WORKOUTS = [ WORKOUT_TYPE_HILL_RIDE, WORKOUT_TYPE_BIKE_CADENCE_DRILLS, WORKOUT_TYPE_SPEED_INTERVAL_RIDE, \
                  WORKOUT_TYPE_TEMPO_RIDE, WORKOUT_TYPE_EASY_RIDE, WORKOUT_TYPE_SWEET_SPOT_RIDE ]
SWIM_WORKOUTS = [ WORKOUT_TYPE_OPEN_WATER_SWIM, WORKOUT_TYPE_POOL_SWIM, WORKOUT_TYPE_TECHNIQUE_SWIM ]

# Interval workouts.
INTERVAL_WORKOUT_REPEAT_KEY = "repeat"
INTERVAL_WORKOUT_DISTANCE_KEY = "distance"
INTERVAL_WORKOUT_DURATION_KEY = "duration"
INTERVAL_WORKOUT_PACE_KEY = "pace"
INTERVAL_WORKOUT_POWER_KEY = "power"
INTERVAL_WORKOUT_RECOVERY_DISTANCE_KEY = "recovery distance"
INTERVAL_WORKOUT_RECOVERY_DURATION_KEY = "recovery duration"
INTERVAL_WORKOUT_RECOVERY_PACE_KEY = "recovery pace"
INTERVAL_WORKOUT_RECOVERY_POWER_KEY = "recovery power"

# Keys associated with uploading data.
UPLOADED_FILE_NAME_KEY = "uploaded_file_name"
UPLOADED_FILE_DATA_KEY = "uploaded_file_data"
UPLOADED_FILE1_DATA_KEY = "uploaded_file1_data"
UPLOADED_FILE2_DATA_KEY = "uploaded_file2_data"

# Keys associated with adding a new race.
RACE_ID_KEY = "Race ID"
RACE_NAME_KEY = "Race Name"
RACE_DATE_KEY = "Race Date"
RACE_DISTANCE_KEY = "Race Distance"
RACE_IMPORTANCE_KEY = "Race Importance"

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
APP_TEMP_KEY = "Temperature" # Raw temperature data
APP_CURRENT_SPEED_KEY = "Current Speed"
APP_AVG_SPEED_KEY = "Avgerage Speed"
APP_MOVING_SPEED_KEY = "Moving Speed" 
APP_SPEED_VARIANCE_KEY = "Speed Variance"
APP_HEART_RATE_KEY = "Heart Rate" # Raw heart rate list.
APP_AVG_HEART_RATE_KEY = "Average Heart Rate" # Computed average heart rate.
APP_CURRENT_PACE_KEY = "Current Pace" # Computed pace list.
APP_POWER_KEY = "Power" # Raw power data list.
APP_THREAT_COUNT_KEY = "Threat Count" # Threat count, like from a cycling radar unit.
APP_EVENTS_KEY = "Events" # Raw event data (gear shifts, etc.)
APP_SETS_KEY = "Sets"
APP_DISTANCES_KEY = "distances" # Distance between data points.
APP_LOCATIONS_KEY = "locations" # Raw position data.
APP_LOCATION_LAT_KEY = "Latitude"
APP_LOCATION_LON_KEY = "Longitude"
APP_LOCATION_ALT_KEY = "Altitude"
APP_HORIZONTAL_ACCURACY_KEY = "Horizontal Accuracy"
APP_VERTICAL_ACCURACY_KEY = "Vertical Accuracy"
APP_ACCELEROMETER_KEY = "accelerometer" # Raw accelerometer list.
APP_AXIS_TIME = "time"
APP_AXIS_NAME_X = "x"
APP_AXIS_NAME_Y = "y"
APP_AXIS_NAME_Z = "z"

LOCATION_LAT_KEY = "latitude"
LOCATION_LON_KEY = "longitude"
LOCATION_ALT_KEY = "altitude"
LOCATION_HORIZONTAL_ACCURACY_KEY = "horizontal accuracy" # Meters
LOCATION_VERTICAL_ACCURACY_KEY = "vertical accuracy" # Meters
LOCATION_TIME_KEY = "time" # UNIX timestamp in milliseconds

ACCELEROMETER_AXIS_NAME_X = "x" # X-axis G force
ACCELEROMETER_AXIS_NAME_Y = "y" # Y-axis G force
ACCELEROMETER_AXIS_NAME_Z = "z" # Z-axis G force
ACCELEROMETER_TIME_KEY = "time" # UNIX timestamp in milliseconds

# Keys inherited from the web app.
ACTIVITY_ID_KEY = "activity_id" # Unique identifier for the activity
ACTIVITY_HASH_KEY = "activity_hash"
ACTIVITY_TYPE_KEY = "activity_type"
ACTIVITY_DESCRIPTION_KEY = "description"
ACTIVITY_USER_ID_KEY = "user_id"
ACTIVITY_DEVICE_STR_KEY = "device_str"
ACTIVITY_LOCATIONS_KEY = "locations"
ACTIVITY_NAME_KEY = "name"
ACTIVITY_START_TIME_KEY = "time" # UNIX timestamp in seconds
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
ACTIVITY_INTERVALS_KEY = "intervals" # Intervals that were computed from the workout
ACTIVITY_PHOTO_ID_KEY = "photo id" # Unique identifier for a specific photo
ACTIVITY_PHOTO_IDS_KEY = "photo ids" # Unique identifier for activity photos
ACTIVITY_PHOTOS_KEY = "photos" # List of all photo IDs
ACTIVITY_LAST_UPDATED_KEY = "last updated" # Time when the activity was last updated

# Keys used to summarize activity data.
BEST_SPEED = "Best Speed" # Highest speed seen during the activity
BEST_PACE = "Best Pace" # Fastest pace seen during the activity
BEST_1K = "Best 1K" # Fastest 1K segment (can be anywhere in the activity)
BEST_MILE = "Best Mile" # Fastest mile segment (can be anywhere in the activity)
BEST_5K = "Best 5K" # Fastest 5K segment (can be anywhere in the activity)
BEST_10K = "Best 10K" # Fastest 10K segment (can be anywhere in the activity)
BEST_15K = "Best 15K" # Fastest 15K segment (can be anywhere in the activity)
BEST_HALF_MARATHON = "Best Half Marathon" # Fastest half marathon segment (can be anywhere in the activity)
BEST_MARATHON = "Best Marathon" # Fastest marathon segment (can be anywhere in the activity)
BEST_METRIC_CENTURY = "Best Metric Century" # Fastest 100K segment (can be anywhere in the activity)
BEST_CENTURY = "Best Century" # Fastest 100 mile segment (can be anywhere in the activity)
BEST_5_SEC_POWER = "5 Second Power" # Highest average power seen over 5 seconds
BEST_12_MIN_POWER = "12 Minute Power" # Highest average power seen over 12 minutes
BEST_20_MIN_POWER = "20 Minute Power" # Highest average power seen over 20 minutes
BEST_1_HOUR_POWER = "1 Hour Power" # Highest average power seen over 1 hour
MAX_POWER = "Maximum Power" # Highest power detected during the activity
MAX_HEART_RATE = "Maximum Heart Rate" # Highest heart rate detected during the activity
MAX_CADENCE = "Maximum Cadence" # Highest recorded cadence
AVG_PACE = "Average Pace" # Average pace of the activity
AVG_POWER = "Average Power" # Average power (watts) held during the activity
AVG_HEART_RATE = "Average Heart Rate" # Average heart rate (bpm) held during the activity
AVG_CADENCE = "Average Cadence" # Average cadence (rpm or spm) held during the activity
STEPS_PER_MINUTE = "Steps Per Minute" # Cadence for foot based activity
AVG_STEPS_PER_MINUTE = "Average Steps Per Minute" # Average cadence for foot based activity
NORMALIZED_POWER = "Normalized Power"
THRESHOLD_POWER = "Threshold Power" # Functional Threshold Power (FTP)
VARIABILITY_INDEX = "Variability Index"
LONGEST_DISTANCE = "Longest Distance" # Longest distance, when summarizing activities
TOTAL_DISTANCE = "Total Distance" # Distance for an activity
TOTAL_DURATION = "Total Duration" # Number of seconds for the activity/activities
TOTAL_ACTIVITIES = "Total Activities" # Number of activities logged over the specified time
INTENSITY_SCORE = "Intensity Score" # Intensity score, represents the intensity of the workout
ESTIMATED_INTENSITY_SCORE = "Estimated Intensity Score" # Estimated intensity score, for activities that don't have power data
TOTAL_INTENSITY_SCORE = "Total Intensity Score" # Sum of the intensity scores for each activity within the specified time
MILE_SPLITS = "Mile Splits" # List of mile splits
KM_SPLITS = "KM Splits" # List of kilometer splits

# Options when trimming activities
TRIM_FROM_KEY = "Trim From"
TRIM_FROM_BEGINNING_VALUE = "Beginning"
TRIM_FROM_END_VALUE = "End"
TRIM_SECONDS_KEY = "Seconds"

# Keys used for race time prediction.
ESTIMATED_5K_KEY = "Estimated 5K"
ESTIMATED_10K_KEY = "Estimated 10K"
ESTIMATED_HALF_MARATHON_KEY = "Estimated Half Marathon"
ESTIMATED_MARATHON_KEY = "Estimated Marathon"

# API-only keys.
SECONDS = "seconds"
DEVICE_LAST_HEARD_FROM_KEY = "last_heard_from" # Time when we last received an activity from the device
DEVICE_LAST_SYNCHED_KEY = "timestamp" # Time when the device last synchronized

# Running paces.
LONG_RUN_PACE = "Long Run Pace"
EASY_RUN_PACE = "Easy Run Pace"
TEMPO_RUN_PACE = "Tempo Run Pace"
FUNCTIONAL_THRESHOLD_PACE = "Functional Threshold Pace" # Pace that could be held for one hour, max effort
SPEED_RUN_PACE = "Speed Session Pace" # Pace for medium distance interfals
SHORT_INTERVAL_RUN_PACE = "Short Interval Run Pace" # Pace for shorter track intervals

# Keys used to manage gear.
GEAR_KEY = "gear"
GEAR_DEFAULTS_KEY = "gear_defaults"
GEAR_ID_KEY = "gear_id"
GEAR_TYPE_KEY = "type"
GEAR_TYPE_BIKE = "bike"
GEAR_TYPE_SHOES = "shoes"
GEAR_NAME_KEY = "name"
GEAR_DESCRIPTION_KEY = "description"
GEAR_ADD_TIME_KEY = "add_time"
GEAR_RETIRE_TIME_KEY = "retire_time"
GEAR_INITIAL_DISTANCE_KEY = "initial_distance"
GEAR_SERVICE_HISTORY_KEY = "service_history"
GEAR_LAST_UPDATED_TIME_KEY = "last_updated_time"

# Service record keys.
SERVICE_RECORD_ID_KEY = "service_id"
SERVICE_RECORD_DATE_KEY = "date"
SERVICE_RECORD_DESCRIPTION_KEY = "description"

# Keys used to manage pace plans.
PACE_PLANS_KEY = "pace_plans"
PACE_PLAN_ID_KEY = "id" # Unique identifier
PACE_PLAN_NAME_KEY = "name" # Plan name
PACE_PLAN_DESCRIPTION_KEY = "description" # Plan description
PACE_PLAN_TARGET_DISTANCE_KEY = "target distance" # Target distance (in target units)
PACE_PLAN_TARGET_DISTANCE_UNITS_KEY = "target distance units" # Units for interpreting the distance value
PACE_PLAN_TARGET_TIME_KEY = "target time" # Target finishing time (in hh:mm:ss format)
PACE_PLAN_TARGET_SPLITS_KEY = "target splits" # Desired splits, in +/- seconds (i.e., zero is even splits)
PACE_PLAN_TARGET_SPLITS_UNITS_KEY = "target splits units" # Units for interpreting the splits sec/mile or sec/km
PACE_PLAN_ROUTE_KEY = "route" # Route file
PACE_PLAN_LAST_UPDATED_KEY = "last updated time" # Last updated timestamp

# Activity types.
TYPE_UNSPECIFIED_ACTIVITY_KEY = "Unknown"
TYPE_RUNNING_KEY = "Running"
TYPE_TRAIL_RUNNING_KEY = "Trail Running"
TYPE_VIRTUAL_RUNNING_KEY = "Virtual Running"
TYPE_INDOOR_RUNNING_KEY = "Indoor Running"
TYPE_TREADMILL_KEY = "Treadmill"
TYPE_HIKING_KEY = "Hiking"
TYPE_WALKING_KEY = "Walking"
TYPE_CYCLING_KEY = "Cycling"
TYPE_INDOOR_CYCLING_KEY = "Indoor Cycling"
TYPE_VIRTUAL_CYCLING_KEY = "Virtual Cycling"
TYPE_MOUNTAIN_BIKING_KEY = "Mountain Biking"
TYPE_GRAVEL_CYCLING_KEY = "Gravel Cycling"
TYPE_CYCLOCROSS_KEY = "Cyclocross"
TYPE_OPEN_WATER_SWIMMING_KEY = "Open Water Swimming"
TYPE_POOL_SWIMMING_KEY = "Pool Swimming"
TYPE_BENCH_PRESS_KEY = "Bench Press"
TYPE_PULL_UP_KEY = "Pull Up"
TYPE_PUSH_UP_KEY = "Push Up"
TYPE_TRIATHLON_KEY = "Triathlon"
TYPE_DUATHLON_KEY = "Duathon"

# Activity type groups.
RUNNING_ACTIVITIES = [ TYPE_RUNNING_KEY, TYPE_INDOOR_RUNNING_KEY, TYPE_TREADMILL_KEY, TYPE_TRAIL_RUNNING_KEY, TYPE_VIRTUAL_RUNNING_KEY ] 
FOOT_BASED_ACTIVITIES = [ TYPE_RUNNING_KEY, TYPE_INDOOR_RUNNING_KEY, TYPE_TREADMILL_KEY, TYPE_TRAIL_RUNNING_KEY, TYPE_VIRTUAL_RUNNING_KEY, TYPE_HIKING_KEY, TYPE_WALKING_KEY ]
CYCLING_ACTIVITIES = [ TYPE_CYCLING_KEY, TYPE_INDOOR_CYCLING_KEY, TYPE_VIRTUAL_CYCLING_KEY, TYPE_MOUNTAIN_BIKING_KEY, TYPE_GRAVEL_CYCLING_KEY, TYPE_CYCLOCROSS_KEY ]
SWIMMING_ACTIVITIES = [ TYPE_OPEN_WATER_SWIMMING_KEY, TYPE_POOL_SWIMMING_KEY ]
STRENGTH_ACTIVITIES = [ TYPE_BENCH_PRESS_KEY, TYPE_PULL_UP_KEY, TYPE_PUSH_UP_KEY ]
MULTISPORT_ACTIVITIES = [ TYPE_TRIATHLON_KEY, TYPE_DUATHLON_KEY ]

# Activity names.
UNNAMED_ACTIVITY_TITLE = "Unnamed"

# Used to track deferred tasks.
TASKS_KEY = "tasks"
TASK_CELERY_ID_KEY = "celery task id"
TASK_INTERNAL_ID_KEY = "internal task id"
TASK_ACTIVITY_ID_KEY = "activity id"
TASK_TYPE_KEY = "task type"
TASK_DETAILS_KEY = "task details"
TASK_STATUS_KEY = "task status"
IMPORT_TASK_KEY = "import"
ANALYSIS_TASK_KEY = "analysis"
WORKOUT_PLAN_TASK_KEY = "workout plan"
TASK_STATUS_QUEUED = "Queued"
TASK_STATUS_STARTED = "Started"
TASK_STATUS_FINISHED = "Finished"
TASK_STATUS_ERROR = "Error"

# Things associated with deferred tasks.
LOCAL_FILE_NAME = "local file name"

# Only used by the API.
DEVICE_ID_KEY = "device_id"
SENSOR_LIST_KEY = "sensors"
SENSOR_NAME_KEY = "sensor_name"
SUMMARY_ITEMS_LIST_KEY = "summary_items"
START_TIME_KEY = "start_time"
END_TIME_KEY = "end_time"
START_DATE_KEY = "start"
END_DATE_KEY = "end"
CODE_KEY = "code" # Used for sync, values are specified below
USER_AGE_IN_YEARS = "age in years" # Some API functions request the user's age in years

# Activity match codes used for sync.
ACTIVITY_MATCH_CODE_NO_ACTIVITY = 0 # Activity does not exist
ACTIVITY_MATCH_CODE_HASH_NOT_COMPUTED = 1  # Activity exists, hash not computed
ACTIVITY_MATCH_CODE_HASH_DOES_NOT_MATCH = 2 # Activity exists, has does not match
ACTIVITY_MATCH_CODE_HASH_MATCHES = 3 # Activity exists, hash matches as well
ACTIVITY_MATCH_CODE_HASH_NOT_PROVIDED = 4  # Activity exists, hash not provided

SENSOR_KEYS = [ APP_CADENCE_KEY, APP_HEART_RATE_KEY, APP_TEMP_KEY, APP_POWER_KEY ]
TIME_KEYS = [ APP_DURATION_KEY, BEST_1K, BEST_MILE, BEST_5K, BEST_10K, BEST_15K, BEST_HALF_MARATHON, BEST_MARATHON, BEST_METRIC_CENTURY, BEST_CENTURY ]
DISTANCE_KEYS = [ TOTAL_DISTANCE, LONGEST_DISTANCE ]
SPEED_KEYS = [ APP_CURRENT_SPEED_KEY, APP_AVG_SPEED_KEY, APP_MOVING_SPEED_KEY, APP_SPEED_VARIANCE_KEY, BEST_SPEED ]
PACE_KEYS = [ APP_CURRENT_PACE_KEY, BEST_PACE, AVG_PACE, LONG_RUN_PACE, EASY_RUN_PACE, TEMPO_RUN_PACE, FUNCTIONAL_THRESHOLD_PACE, SPEED_RUN_PACE, SHORT_INTERVAL_RUN_PACE, FUNCTIONAL_THRESHOLD_PACE, INTERVAL_WORKOUT_PACE_KEY ]
POWER_KEYS = [ AVG_POWER, MAX_POWER, BEST_5_SEC_POWER, BEST_12_MIN_POWER, BEST_20_MIN_POWER, BEST_1_HOUR_POWER, NORMALIZED_POWER, THRESHOLD_POWER ]
HEART_RATE_KEYS = [ AVG_HEART_RATE, MAX_HEART_RATE ]
CADENCE_KEYS = [ APP_CADENCE_KEY, AVG_CADENCE, MAX_CADENCE ]
RUNNING_CADENCE_KEYS = [ STEPS_PER_MINUTE, AVG_STEPS_PER_MINUTE ]
GOALS = [ GOAL_FITNESS_KEY, GOAL_5K_RUN_KEY, GOAL_10K_RUN_KEY, GOAL_15K_RUN_KEY, GOAL_HALF_MARATHON_RUN_KEY, GOAL_MARATHON_RUN_KEY, GOAL_50K_RUN_KEY, GOAL_50_MILE_RUN_KEY, GOAL_SPRINT_TRIATHLON_KEY, GOAL_OLYMPIC_TRIATHLON_KEY, GOAL_HALF_IRON_DISTANCE_TRIATHLON_KEY, GOAL_IRON_DISTANCE_TRIATHLON_KEY ]
INTENSITY_SCORES = [ INTENSITY_SCORE, ESTIMATED_INTENSITY_SCORE, TOTAL_INTENSITY_SCORE ]

UNSUMMARIZABLE_KEYS = [ APP_SPEED_VARIANCE_KEY, APP_DISTANCES_KEY, APP_LOCATIONS_KEY, ACTIVITY_START_TIME_KEY, ACTIVITY_TYPE_KEY, ACTIVITY_HASH_KEY, ACTIVITY_LOCATION_DESCRIPTION_KEY, ACTIVITY_INTERVALS_KEY, MILE_SPLITS, KM_SPLITS ]

DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
