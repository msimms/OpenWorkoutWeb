# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Michael J Simms
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
"""Unit conversion routines."""

import Keys

UNITS_MASS_KG = 1
UNITS_MASS_POUNDS = 2

UNITS_DISTANCE_METERS = 1
UNITS_DISTANCE_KILOMETERS = 2
UNITS_DISTANCE_MILES = 3
UNITS_DISTANCE_FEET = 4
UNITS_DISTANCE_INCHES = 5

UNITS_TIME_SECONDS = 1
UNITS_TIME_MINUTES = 2
UNITS_TIME_HOURS = 3

METERS_PER_MILE = 1609.34
FEET_PER_MILE = 5280.0
FEET_PER_METER = 3.28084
INCHES_PER_METER = 39.3701
INCHES_PER_FOOT = 12.0
KGS_PER_POUND = 2.2

SECS_PER_DAY = 86400

METERS_PER_HALF_MARATHON = 13.1 * METERS_PER_MILE
METERS_PER_MARATHON = 26.2 * METERS_PER_MILE
METERS_PER_50_MILE = 50.0 * METERS_PER_MILE

def convert_mass(value, in_units, out_units):
    """Unit conversion for mass values."""
    if in_units == UNITS_MASS_KG:
        if out_units == UNITS_MASS_POUNDS:
            return value * KGS_PER_POUND
    elif in_units == UNITS_MASS_POUNDS:
        if out_units == UNITS_MASS_KG:
            return value / KGS_PER_POUND
    return value

def convert_distance(value, in_units, out_units):
    """Unit conversion for distance values."""
    if in_units == UNITS_DISTANCE_METERS:
        if out_units == UNITS_DISTANCE_KILOMETERS:
            return value / 1000.0
        elif out_units == UNITS_DISTANCE_MILES:
            return value / METERS_PER_MILE
        elif out_units == UNITS_DISTANCE_FEET:
            return value / METERS_PER_MILE / FEET_PER_MILE
        elif out_units == UNITS_DISTANCE_INCHES:
            return value * INCHES_PER_METER
    elif in_units == UNITS_DISTANCE_KILOMETERS:
        if out_units == UNITS_DISTANCE_METERS:
            return value * 1000.0
        elif out_units == UNITS_DISTANCE_MILES:
            return value * (METERS_PER_MILE / 1000.0)
        elif out_units == UNITS_DISTANCE_FEET:
            return value * (METERS_PER_MILE / 1000.0 / FEET_PER_MILE)
        elif out_units == UNITS_DISTANCE_INCHES:
            return value * 1000.0 * INCHES_PER_METER
    elif in_units == UNITS_DISTANCE_MILES:
        if out_units == UNITS_DISTANCE_METERS:
            return value * METERS_PER_MILE
        elif out_units == UNITS_DISTANCE_KILOMETERS:
            return value / (METERS_PER_MILE / 1000.0)
        elif out_units == UNITS_DISTANCE_FEET:
            return value * FEET_PER_MILE
        elif out_units == UNITS_DISTANCE_INCHES:
            return value * FEET_PER_MILE * INCHES_PER_FOOT
    elif in_units == UNITS_DISTANCE_FEET:
        if out_units == UNITS_DISTANCE_METERS:
            return value / FEET_PER_METER
        elif out_units == UNITS_DISTANCE_INCHES:
            return value * INCHES_PER_FOOT
    elif in_units == UNITS_DISTANCE_INCHES:
        if out_units == UNITS_DISTANCE_METERS:
            return value / INCHES_PER_METER
        elif out_units == UNITS_DISTANCE_FEET:
            return value / INCHES_PER_FOOT
    return value

def convert_to_distance_for_the_specified_unit_system(unit_system, value, in_units):
    """Unit conversion for distance values. Converts to either metric or standard, depending on which is specified."""
    if unit_system == Keys.UNITS_METRIC_KEY:
        if value < 1000:
            out_units = UNITS_DISTANCE_METERS
        else:
            out_units = UNITS_DISTANCE_KILOMETERS
    else:
        out_units = UNITS_DISTANCE_MILES
    return convert_distance(value, in_units, out_units), out_units

def convert_time(value, in_units, out_units):
    """Unit conversion for time values."""
    if in_units == UNITS_TIME_SECONDS:
        if out_units == UNITS_TIME_MINUTES:
            return value / 60.0
        elif out_units == UNITS_TIME_HOURS:
            return value / 60.0 / 60.0
    elif in_units == UNITS_TIME_MINUTES:
        if out_units == UNITS_TIME_SECONDS:
            return value * 60.0
        elif out_units == UNITS_TIME_HOURS:
            return value / 60.0
    elif in_units == UNITS_TIME_HOURS:
        if out_units == UNITS_TIME_SECONDS:
            return value * 60.0 * 60.0
        elif out_units == UNITS_TIME_MINUTES:
            return value * 60.0
    return value

def convert_speed(value, in_distance_units, in_time_units, out_distance_units, out_time_units):
    """Unit conversion for speed values."""
    value = convert_distance(value, in_distance_units, out_distance_units)
    if in_time_units == UNITS_TIME_SECONDS:
        if out_time_units == UNITS_TIME_MINUTES:
            return value * 60.0
        elif out_time_units == UNITS_TIME_HOURS:
            return value * 60.0 * 60.0
    elif in_time_units == UNITS_TIME_MINUTES:
        if out_time_units == UNITS_TIME_SECONDS:
            return value / 60.0
        elif out_time_units == UNITS_TIME_HOURS:
            return value * 60.0
    elif in_time_units == UNITS_TIME_HOURS:
        if out_time_units == UNITS_TIME_SECONDS:
            return value / 60.0 / 60.0
        elif out_time_units == UNITS_TIME_MINUTES:
            return value / 60.0
    return value

def convert_to_speed_for_the_specified_unit_system(unit_system, value, in_distance_units, in_time_units):
    """Unit conversion for speed values. Converts to either metric or standard, depending on which is specified."""
    out_time_units = UNITS_TIME_HOURS
    if unit_system == Keys.UNITS_METRIC_KEY:
        out_distance_units = UNITS_DISTANCE_KILOMETERS
    else:
        out_distance_units = UNITS_DISTANCE_MILES
    return convert_speed(value, in_distance_units, in_time_units, out_distance_units, out_time_units), out_distance_units, out_time_units

def convert_to_pace_for_the_specified_unit_system(unit_system, value, in_distance_units, in_time_units):
    """Unit conversion for pace values. Converts to either metric or standard, depending on the user's preferences."""
    out_time_units = UNITS_TIME_MINUTES
    if unit_system == Keys.UNITS_METRIC_KEY:
        out_distance_units = UNITS_DISTANCE_KILOMETERS
    else:
        out_distance_units = UNITS_DISTANCE_MILES

    speed = convert_speed(value, in_distance_units, in_time_units, out_distance_units, out_time_units)
    if speed < 0.001:
        return 0.0, out_distance_units, out_time_units

    pace = 1.0 / speed
    return pace, out_distance_units, out_time_units

def meters_per_sec_to_minutes_per_mile(value):
    speed = convert_speed(value, UNITS_DISTANCE_METERS, UNITS_TIME_SECONDS, UNITS_DISTANCE_MILES, UNITS_TIME_MINUTES)
    if speed < 0.001:
        return 0.0
    return 1.0 / speed

def meters_per_sec_to_minutes_per_kilometers(value):
    speed = convert_speed(value, UNITS_DISTANCE_METERS, UNITS_TIME_SECONDS, UNITS_DISTANCE_KILOMETERS, UNITS_TIME_MINUTES)
    if speed < 0.001:
        return 0.0
    return 1.0 / speed

def get_mass_units_str(mass_units):
    """Returns the units in which mass is displayed."""
    if mass_units == UNITS_MASS_KG:
        return "kgs"
    elif mass_units == UNITS_MASS_POUNDS:
        return "lbs"
    return ""

def get_preferred_mass_units_str(user_mgr, user_id):
    """Returns the units in which mass is displayed."""
    selected_units = user_mgr.retrieve_user_setting(user_id, Keys.USER_PREFERRED_UNITS_KEY)
    if selected_units is not Keys.UNITS_METRIC_KEY:
        return get_mass_units_str(UNITS_MASS_POUNDS)
    return get_mass_units_str(UNITS_MASS_KG)

def get_distance_units_str(distance_units):
    """Returns the units in which distance is displayed."""
    if distance_units == UNITS_DISTANCE_METERS:
        return "meters"
    elif distance_units == UNITS_DISTANCE_KILOMETERS:
        return "kms"
    elif distance_units == UNITS_DISTANCE_MILES:
        return "miles"
    elif distance_units == UNITS_DISTANCE_FEET:
        return "feet"
    elif distance_units == UNITS_DISTANCE_INCHES:
        return "inches"
    return ""

def get_preferred_height_units_str(user_mgr, user_id):
    """Returns the units in which height is displayed."""
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.USER_PREFERRED_UNITS_KEY)
        if selected_units is not Keys.UNITS_METRIC_KEY:
            return get_distance_units_str(UNITS_DISTANCE_INCHES)
    return get_distance_units_str(UNITS_DISTANCE_METERS)

def get_speed_units_str(distance_units, time_units):
    """Returns the units in which speed is displayed."""
    units_str = get_distance_units_str(distance_units)
    units_str = units_str + " / "

    if time_units == UNITS_TIME_MINUTES:
        units_str = units_str + "min"
    elif time_units == UNITS_TIME_SECONDS:
        units_str = units_str + "sec"
    elif time_units == UNITS_TIME_HOURS:
        units_str = units_str + "hour"
    return units_str

def get_pace_units_str(distance_units, time_units):
    """Returns the units in which pace is displayed."""
    units_str = ""

    if time_units == UNITS_TIME_MINUTES:
        units_str = "mins"
    elif time_units == UNITS_TIME_SECONDS:
        units_str = "secs"
    elif time_units == UNITS_TIME_HOURS:
        units_str = "hours"

    units_str = units_str + " / "

    if distance_units == UNITS_DISTANCE_METERS:
        units_str = units_str + "meter"
    elif distance_units == UNITS_DISTANCE_KILOMETERS:
        units_str = units_str + "km"
    elif distance_units == UNITS_DISTANCE_MILES:
        units_str = units_str + "mile"
    return units_str

def convert_seconds_to_hours_mins_secs(seconds_in):
    """Converts seconds to HH:MM:SS format."""
    temp_seconds = int(seconds_in)
    seconds = temp_seconds % 60
    minutes = temp_seconds / 60
    hours = minutes / 60
    minutes = minutes % 60
    out_str = "{:0>2d}:{:0>2d}:{:0>2d}".format(int(hours), int(minutes), int(seconds))
    return out_str

def convert_seconds_to_mins_secs(seconds_in):
    """Converts seconds to MM:SS format."""
    temp_seconds = int(seconds_in)
    seconds = temp_seconds % 60
    minutes = temp_seconds / 60
    minutes = minutes % 60
    out_str = "{:0>2d}:{:0>2d}".format(int(minutes), int(seconds))
    return out_str

def convert_seconds_to_mins_or_secs(seconds_in):
    """Converts seconds to either the number of minutes, or seconds, whichever looks best, i.e. 120 sec becomes 2 minutes, but 39 stays as 39 seconds."""
    temp_seconds = int(seconds_in)
    seconds = int(temp_seconds % 60)
    minutes = temp_seconds / 60
    minutes = int(minutes % 60)
    if minutes > 1 and seconds == 0:
        out_str = "{:d} minutes".format(minutes)
    elif minutes == 1 and seconds == 0:
        out_str = "{:d} minute".format(minutes)
    else:
        out_str = "{:d} seconds".format(seconds)
    return out_str

def convert_minutes_to_mins_secs(minutes_in):
    """Converts minutes to MM:SS format."""
    minutes = int(minutes_in)
    seconds = int((minutes_in - minutes) * 60)
    out_str = "{:0>2d}:{:0>2d}".format(minutes, seconds)
    return out_str

def convert_meters_to_printable(unit_system, meters):
    """Takes a value in meters and, for short distances, returns meters and for longer distance returns in the preferred units, with a label."""
    out_str = ""
    if meters > 1000:
        if unit_system:
            out_str += convert_to_string_in_specified_unit_system(unit_system, meters, UNITS_DISTANCE_METERS, None, Keys.TOTAL_DISTANCE)
        else:
            out_str += convert_to_string_in_specified_unit_system(Keys.UNITS_METRIC_KEY, meters, UNITS_DISTANCE_METERS, None, Keys.TOTAL_DISTANCE)
            out_str += " ("
            out_str += convert_to_string_in_specified_unit_system(Keys.UNITS_STANDARD_KEY, meters, UNITS_DISTANCE_METERS, None, Keys.TOTAL_DISTANCE)
            out_str += ")"
    elif meters > 0:
        out_str += str(int(meters))
        out_str += " meters"
    return out_str

def get_heart_rate_units_str():
    """Returns the units in which heart rate is displayed."""
    return "bpm"

def get_cadence_units_str():
    """Returns the units in which cadence is displayed."""
    return "rpm"

def get_running_cadence_units_str():
    """Returns the units in which running cadence is displayed."""
    return "spm"

def get_power_units_str():
    """Returns the units in which power is displayed."""
    return "watts"

def convert_to_string_in_specified_unit_system(unit_system, in_value, in_distance_units, in_time_units, label):
    """Generic unit conversion routine. Returns a string with the converted number and units."""
    """Call this function when you need to make something pretty before displaying it to the user."""
    out_value = in_value
    if label in Keys.TIME_KEYS:
        out_value = convert_seconds_to_hours_mins_secs(in_value)
    elif label in Keys.DISTANCE_KEYS:
        out_value, out_distance_units = convert_to_distance_for_the_specified_unit_system(unit_system, in_value, in_distance_units)
        out_value = "{:.2f} ".format(out_value) + get_distance_units_str(out_distance_units)
    elif label in Keys.SPEED_KEYS:
        out_value, out_distance_units, out_time_units = convert_to_speed_for_the_specified_unit_system(unit_system, in_value, in_distance_units, in_time_units)
        out_value = "{:.2f} ".format(out_value) + get_speed_units_str(out_distance_units, out_time_units)
    elif label in Keys.PACE_KEYS:
        out_value, out_distance_units, out_time_units = convert_to_pace_for_the_specified_unit_system(unit_system, in_value, in_distance_units, in_time_units)
        out_value = convert_minutes_to_mins_secs(out_value) + " " + get_pace_units_str(out_distance_units, out_time_units)
    elif label in Keys.HEART_RATE_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_heart_rate_units_str()
    elif label in Keys.CADENCE_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_cadence_units_str()
    elif label in Keys.RUNNING_CADENCE_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_running_cadence_units_str()
    elif label in Keys.POWER_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_power_units_str()
    elif label in Keys.INTENSITY_SCORES:
        out_value = "{:.2f} ".format(in_value)
    elif label == Keys.VARIABILITY_INDEX:
        out_value = "{:.2f} ".format(in_value)
    else:
        out_value = str(in_value)
    return out_value

def convert_to_num_in_specified_unit_system(unit_system, in_value, in_distance_units, in_time_units, label):
    """Generic unit conversion routine. Returns a number with the converted value."""
    out_value = in_value
    if label in Keys.TIME_KEYS:
        out_value = convert_seconds_to_hours_mins_secs(in_value)
    elif label in Keys.DISTANCE_KEYS:
        out_value, _ = convert_to_distance_for_the_specified_unit_system(unit_system, in_value, in_distance_units)
    elif label in Keys.SPEED_KEYS:
        out_value, _, _ = convert_to_speed_for_the_specified_unit_system(unit_system, in_value, in_distance_units, in_time_units)
    elif label in Keys.PACE_KEYS:
        out_value, _, _ = convert_to_pace_for_the_specified_unit_system(unit_system, in_value, in_distance_units, in_time_units)
    elif label in Keys.HEART_RATE_KEYS:
        out_value = in_value
    elif label in Keys.CADENCE_KEYS:
        out_value = in_value
    elif label in Keys.RUNNING_CADENCE_KEYS:
        out_value = in_value
    elif label in Keys.POWER_KEYS:
        out_value = in_value
    else:
        out_value = in_value
    return out_value
