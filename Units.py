# Copyright 2018 Michael J Simms

import Keys
import UserMgr

UNITS_DISTANCE_METERS = 1
UNITS_DISTANCE_KILOMETERS = 2
UNITS_DISTANCE_MILES = 3
UINTS_DISTANCE_FEET = 4

UNITS_TIME_SECONDS = 1
UNITS_TIME_MINUTES = 2
UNITS_TIME_HOURS = 3

METERS_PER_MILE = 1609.34
FEET_PER_MILE = 5280.0

def convert_distance(value, in_units, out_units):
    """Unit conversion for distance values."""
    if in_units == UNITS_DISTANCE_METERS:
        if out_units == UNITS_DISTANCE_KILOMETERS:
            return value / 1000.0
        elif out_units == UNITS_DISTANCE_MILES:
            return value / METERS_PER_MILE
        elif out_units == UINTS_DISTANCE_FEET:
            return value / METERS_PER_MILE / FEET_PER_MILE
    elif in_units == UNITS_DISTANCE_KILOMETERS:
        if out_units == UNITS_DISTANCE_METERS:
            return value * 1000.0
        elif out_units == UNITS_DISTANCE_MILES:
            return value * (METERS_PER_MILE / 1000.0)
        elif out_units == UINTS_DISTANCE_FEET:
            return value * (METERS_PER_MILE / 1000.0 / FEET_PER_MILE)
    elif in_units == UNITS_DISTANCE_MILES:
        if out_units == UNITS_DISTANCE_METERS:
            return value * METERS_PER_MILE
        elif out_units == UNITS_DISTANCE_KILOMETERS:
            return value / (METERS_PER_MILE / 1000.0)
        elif out_units == UINTS_DISTANCE_FEET:
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

def get_distance_units_str(distance_units):
    """Returns the units in which distance is displayed."""
    if distance_units == UNITS_DISTANCE_METERS:
        return "meters"
    elif distance_units == UNITS_DISTANCE_KILOMETERS:
        return "kms"
    elif distance_units == UNITS_DISTANCE_MILES:
        return "miles"
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

def get_heart_rate_units_str():
    """Returns the units in which heart rate is displayed."""
    return "bpm"

def get_cadence_units_str():
    """Returns the units in which cadence is displayed."""
    return "rpm"

def get_power_units_str():
    """Returns the units in which power is displayed."""
    return "watts"
