// -*- coding: utf-8 -*-
// 
// MIT License
// 
// Copyright (c) 2020 Mike Simms
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

function degrees_to_radians(degrees)
{
    let pi = Math.PI;
    return degrees * (pi/180);
}

/// @function Calculates the distance between two points on the earth's surface.
function haversine_distance(loc1_lat, loc1_lon, loc1_alt, loc2_lat, loc2_lon, loc2_alt)
{
    // Returns the Haversine distance between two points on the Earth's surface.
    R = 6372797.560856; // radius of the earth in meters
    R = R + loc2_alt - loc1_alt;

    lat_arc = degrees_to_radians(loc1_lat - loc2_lat);
    lon_arc = degrees_to_radians(loc1_lon - loc2_lon);

    lat_h = Math.sin(lat_arc * 0.5);
    lat_h = lat_h * lat_h;

    lon_h = Math.sin(lon_arc * 0.5);
    lon_h = lon_h * lon_h;

    tmp = Math.cos(degrees_to_radians(loc1_lat)) * Math.cos(degrees_to_radians(loc2_lat));
    rad = 2.0 * Math.asin(Math.sqrt(lat_h + tmp * lon_h));

    return rad * R;
}

/// @function Calculates the distance between two points on the earth's surface, ignores altitude.
function haversine_distance_ignore_altitude(loc1_lat, loc1_lon, loc2_lat, loc2_lon)
{
    // Returns the Haversine distance between two points on the Earth's surface."""
    R = 6372797.560856; // radius of the earth in meters

    lat_arc = degrees_to_radians(loc1_lat - loc2_lat);
    lon_arc = degrees_to_radians(loc1_lon - loc2_lon);

    lat_h = Math.sin(lat_arc * 0.5);
    lat_h = lat_h * lat_h;

    lon_h = Math.sin(lon_arc * 0.5);
    lon_h = lon_h * lon_h;

    tmp = Math.cos(degrees_to_radians(loc1_lat)) * Math.cos(degrees_to_radians(loc2_lat));
    rad = 2.0 * Math.asin(Math.sqrt(lat_h + tmp * lon_h));

    return rad * R;
}

/// @function Distance calculation for a coordinate array that was built for use with the Google Maps API.
function total_distance_google(coordinates)
{
    let last_coordinate = null;
    let total_distance_meters = 0.0;

    for (let coordinate of coordinates)
    {
        if (last_coordinate != null)
        {
            let meters_traveled = haversine_distance_ignore_altitude(coordinate.lat(), coordinate.lng(), last_coordinate.lat(), last_coordinate.lng());
            total_distance_meters += meters_traveled;
        }
        last_coordinate = coordinate;
    }
    return total_distance_meters;
}

/// @function Distance calculation for a coordinate array that was built for use with the Open Street Map API.
function total_distance_osm(coordinates)
{
    let last_coordinate = null;
    let total_distance_meters = 0.0;

    for (let coordinate of coordinates)
    {
        if (last_coordinate != null)
        {
            let meters_traveled = haversine_distance_ignore_altitude(coordinate.y, coordinate.x, last_coordinate.y, last_coordinate.x);
            total_distance_meters += meters_traveled;
        }
        last_coordinate = coordinate;
    }
    return total_distance_meters;
}

/// Converts meters to whatever the preferred units are and formats it as a string.
function convert_distance_to_unit_system_str(unit_system, meters_traveled)
{
    if (unit_system == "metric")
    {
        let km = meters_traveled / 1000.0;
        return km.toFixed(2).toString() + " kms";
    }
    let miles = meters_traveled * 0.000621371;
    return miles.toFixed(2).toString() + " miles";
}

function convert_distance_and_duration_to_pace_str(unit_system, meters_traveled, duration_ms)
{
    if (meters_traveled == 0)
    {
        return "--";
    }

    let pace = 0.0;
    let units = "";

    if (unit_system == "metric")
    {
        let km = meters_traveled / 1000.0;
        pace = (duration_ms / 1000.0 / 60.0) / km;
        units = " min/km";
    }
    else
    {
        let miles = meters_traveled * 0.000621371;
        pace = (duration_ms / 1000.0 / 60.0) / miles;
        units = " min/mile";
    }

    let mins = Math.trunc(pace);
    let secs = (pace - mins) * 60.0;
    let secs_str = secs.toFixed(1).toString().padStart(4, '0');
    return mins.toString() + ":" + secs_str + units;
}

function convert_distance_and_duration_to_speed_str(unit_system, meters_traveled, duration_ms)
{
    if (meters_traveled == 0)
    {
        return "--";
    }

    let speed = 0.0;
    let units = "";

    if (unit_system == "metric")
    {
        let km = meters_traveled / 1000.0;
        speed = km / (duration_ms / 1000.0 / 60.0 / 60.0);
        units = " kph";
    }
    else
    {
        let miles = meters_traveled * 0.000621371;
        speed = miles / (duration_ms / 1000.0 / 60.0 / 60.0);
        units = " mph";
    }
    return speed.toFixed(2).toString() + units;
}
