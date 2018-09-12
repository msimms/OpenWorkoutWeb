# Copyright 2018 Michael J Simms

UNITS_DISTANCE_METERS = 1
UNITS_DISTANCE_KILOMETERS = 2
UNITS_DISTANCE_MILES = 3

UNITS_TIME_SECONDS = 1
UNITS_TIME_MINUTES = 2
UNITS_TIME_HOURS = 3

METERS_PER_MILE = 1609.34

def convert_speed(value, in_distance_units, in_time_units, out_distance_units, out_time_units):
    """Unit conversion for speed values."""

    # Convert the numerator.
    if in_distance_units == UNITS_DISTANCE_METERS:
        if out_distance_units == UNITS_DISTANCE_KILOMETERS:
            value = value / 1000.0
        elif out_distance_units == UNITS_DISTANCE_MILES:
            value = value / METERS_PER_MILE
    elif in_distance_units == UNITS_DISTANCE_KILOMETERS:
        if out_distance_units == UNITS_DISTANCE_METERS:
            value = value * 1000.0
        elif out_distance_units == UNITS_DISTANCE_MILES:
            value = value * (METERS_PER_MILE / 1000.0)
    elif in_distance_units == UNITS_DISTANCE_MILES:
        if out_distance_units == UNITS_DISTANCE_METERS:
            value = value * METERS_PER_MILE
        elif out_distance_units == UNITS_DISTANCE_KILOMETERS:
            value = value / (METERS_PER_MILE / 1000.0)

    # Convert the denominator.
    if in_time_units == UNITS_TIME_SECONDS:
        if out_time_units == UNITS_TIME_MINUTES:
            value = value * 60.0
        elif out_time_units == UNITS_TIME_HOURS:
            value = value * 60.0 * 60.0
    elif in_time_units == UNITS_TIME_MINUTES:
        if out_time_units == UNITS_TIME_SECONDS:
            value = value / 60.0
        elif out_time_units == UNITS_TIME_HOURS:
            value = value * 60.0
    elif in_time_units == UNITS_TIME_HOURS:
        if out_time_units == UNITS_TIME_SECONDS:
            value = value / 60.0 / 60.0
        elif out_time_units == UNITS_TIME_MINUTES:
            value = value / 60.0
    return value

def get_speed_units_str(distance_units, time_units):
    """Returns the units in which speed is displayed."""
    units_str = ""

    if distance_units == UNITS_DISTANCE_METERS:
        units_str = "meters"
    elif distance_units == UNITS_DISTANCE_KILOMETERS:
        units_str = "kms"
    elif distance_units == UNITS_DISTANCE_MILES:
        units_str = "miles"

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
