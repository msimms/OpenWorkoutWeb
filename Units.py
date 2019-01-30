# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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
import UserMgr

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
KGS_PER_POUND = 2.2

def convert_mass(value, in_units, out_units):
    """Unit conversion for mass values."""
    if in_units == UNITS_MASS_KG:
        if out_units == UNITS_MASS_POUNDS:
            return value * KGS_PER_POUND
    elif in_units == UNITS_MASS_POUNDS:
        if out_units == UNITS_MASS_KG:
            return value / KGS_PER_POUND
    return value

def convert_to_preferred_mass_units(user_mgr, user_id, value, in_units):
    """Unit conversion for mass values. Converts to either metric or standard, depending on the user's preferences."""
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)
        if selected_units == Keys.UNITS_METRIC_KEY:
            out_units = UNITS_MASS_KG
        else:
            out_units = UNITS_MASS_POUNDS
    else:
        out_units = UNITS_MASS_KG
    return convert_mass(value, in_units, out_units), out_units

def convert_from_preferred_mass_units(user_mgr, user_id, value):
    """Unit conversion for mass values. Converts from either metric or standard, depending on the user's preferences, to metric."""
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)
        if selected_units == Keys.UNITS_METRIC_KEY:
            in_units = UNITS_MASS_KG
        else:
            in_units = UNITS_MASS_POUNDS
    else:
        in_units = UNITS_MASS_KG
    return convert_mass(value, in_units, UNITS_MASS_KG), UNITS_MASS_KG

def convert_distance(value, in_units, out_units):
    """Unit conversion for distance values."""
    if in_units == UNITS_DISTANCE_METERS:
        if out_units == UNITS_DISTANCE_KILOMETERS:
            return value / 1000.0
        elif out_units == UNITS_DISTANCE_MILES:
            return value / METERS_PER_MILE
        elif out_units == UNITS_DISTANCE_FEET:
            return value / METERS_PER_MILE / FEET_PER_MILE
    elif in_units == UNITS_DISTANCE_KILOMETERS:
        if out_units == UNITS_DISTANCE_METERS:
            return value * 1000.0
        elif out_units == UNITS_DISTANCE_MILES:
            return value * (METERS_PER_MILE / 1000.0)
        elif out_units == UNITS_DISTANCE_FEET:
            return value * (METERS_PER_MILE / 1000.0 / FEET_PER_MILE)
    elif in_units == UNITS_DISTANCE_MILES:
        if out_units == UNITS_DISTANCE_METERS:
            return value * METERS_PER_MILE
        elif out_units == UNITS_DISTANCE_KILOMETERS:
            return value / (METERS_PER_MILE / 1000.0)
        elif out_units == UNITS_DISTANCE_FEET:
            return value / (METERS_PER_MILE / 1000.0 / FEET_PER_MILE)
    return value

def convert_to_preferred_distance_units(user_mgr, user_id, value, in_units):
    """Unit conversion for distance values. Converts to either metric or standard, depending on the user's preferences."""
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)
        if selected_units == Keys.UNITS_METRIC_KEY:
            if value < 1000:
                out_units = UNITS_DISTANCE_METERS
            else:
                out_units = UNITS_DISTANCE_KILOMETERS
        else:
            out_units = UNITS_DISTANCE_MILES
    else:
        out_units = UNITS_DISTANCE_MILES
    return convert_distance(value, in_units, out_units), out_units

def convert_from_preferred_height_units(user_mgr, user_id, value):
    """Unit conversion for height values. Converts from either metric or standard, depending on the user's preferences, to metric."""
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)
        if selected_units == Keys.UNITS_METRIC_KEY:
            in_units = UNITS_DISTANCE_METERS
        else:
            in_units = UNITS_DISTANCE_FEET
    else:
        in_units = UNITS_MASS_KG
    return convert_distance(value, in_units, UNITS_DISTANCE_METERS), UNITS_DISTANCE_METERS

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

def convert_to_preferred_speed_units(user_mgr, user_id, value, in_distance_units, in_time_units):
    """Unit conversion for speed values. Converts to either metric or standard, depending on the user's preferences."""
    out_time_units = UNITS_TIME_HOURS
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)
        if selected_units == Keys.UNITS_METRIC_KEY:
            out_distance_units = UNITS_DISTANCE_KILOMETERS
        else:
            out_distance_units = UNITS_DISTANCE_MILES
    else:
        out_distance_units = UNITS_DISTANCE_MILES
    return convert_speed(value, in_distance_units, in_time_units, out_distance_units, out_time_units), out_distance_units, out_time_units

def meters_per_sec_to_minutes_per_mile(value):
    return 1.0 / convert_speed(value, UNITS_DISTANCE_METERS, UNITS_TIME_SECONDS, UNITS_DISTANCE_MILES, UNITS_TIME_MINUTES)

def meters_per_sec_to_minutes_per_kilometers(value):
    return 1.0 / convert_speed(value, UNITS_DISTANCE_METERS, UNITS_TIME_SECONDS, UNITS_DISTANCE_KILOMETERS, UNITS_TIME_MINUTES)

def get_mass_units_str(mass_units):
    """Returns the units in which mass is displayed."""
    if mass_units == UNITS_MASS_KG:
        return "kgs"
    elif mass_units == UNITS_MASS_POUNDS:
        return "lbs"
    return ""

def get_preferred_mass_units_str(user_mgr, user_id):
    """Returns the units in which mass is displayed."""
    if user_id is not None:
        selected_units = user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)
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
    out_str = "{:0>2d}:{:0>2d}:{:0>2d}".format(hours, minutes, seconds)
    return out_str

def get_heart_rate_units_str():
    """Returns the units in which heart rate is displayed."""
    return "bpm"

def get_cadence_units_str():
    """Returns the units in which cadence is displayed."""
    return "rpm"

def get_power_units_str():
    """Returns the units in which power is displayed."""
    return "watts"

def convert_to_preferred_units_str(user_mgr, user_id, in_value, in_distance_units, in_time_units, label):
    """Generic unit conversion routine. Returns a string with the converted number and units."""
    out_value = in_value
    if label in Keys.TIME_KEYS:
        out_value = convert_seconds_to_hours_mins_secs(in_value)
    elif label in Keys.SPEED_KEYS:
        out_value, out_distance_units, out_time_units = convert_to_preferred_speed_units(user_mgr, user_id, in_value, in_distance_units, in_time_units)        
        out_value = "{:.2f} ".format(out_value) + get_speed_units_str(out_distance_units, out_time_units)
    elif label in Keys.HEART_RATE_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_heart_rate_units_str()
    elif label in Keys.CADENCE_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_heart_rate_units_str()
    elif label in Keys.POWER_KEYS:
        out_value = "{:.2f} ".format(in_value) + get_power_units_str()
    else:
        out_value = str(in_value)
    return out_value
