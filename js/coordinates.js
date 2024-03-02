// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2020 Michael J Simms
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

/// @function degrees_to_radians
function degrees_to_radians(degrees)
{
    let pi = Math.PI;
    return degrees * (pi/180);
}

/// @function haversine_distance
/// Calculates the distance between two points on the earth's surface.
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

/// @function haversine_distance_ignore_altitude
/// Calculates the distance between two points on the earth's surface, ignores altitude.
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

/// @function total_distance_google
/// Distance calculation for a coordinate array that was built for use with the Google Maps API.
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

/// @function total_distance_osm
/// Distance calculation for a coordinate array that was built for use with the Open Street Map API.
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

/// @functionconvert_distance_to_unit_system_str
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

/// @function convert_distance_and_duration_to_pace_str
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

/// @function convert_distance_and_duration_to_speed_str
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

/// @function convert_speed_graph_to_display_units
function convert_speed_graph_to_display_units(unit_system, speed_list)
{
    let new_speed_list = [];

    // Speed is in meters/second.
    let is_metric = (unit_system == "metric");
    for (let data_point in speed_list)
    {
        let date = speed_list[data_point].date;
        let speed = speed_list[data_point].value;
        let value = 0.0;

        if (is_metric)
            value = speed * 3.6;
        else
            value = speed * 2.23694;
        new_speed_list.push({date, value});
    }
    return new_speed_list;
}

/// @function convert_speed_graph_to_pace_graph
function convert_speed_graph_to_pace_graph(unit_system, speed_list)
{
    let pace_list = [];

    // Speed is in meters/second.
    let is_metric = (unit_system == "metric");
    for (let data_point in speed_list)
    {
        let date = speed_list[data_point].date;
        let speed = speed_list[data_point].value;
        let value = 0.0;

        if (speed > 1.0)
        {
            if (is_metric)
                value = 16.6666667 / speed;
            else
                value = 26.8224 / speed;
        }
        else
            value = 0.0;
        pace_list.push({date, value});
    }
    return pace_list;
}

/// @function compute_grade_adjusted_pace
function compute_grade_adjusted_pace(gradient_list, time_pace_data)
{
    let num_gradients = gradient_list.length;
    let gap_list = time_pace_data.map(function(x, i) {
        if (i < num_gradients)
        {
            let pace = x.value;

            if (pace > 0.1)
            {
                let gradient = gradient_list[i];

                if (gradient > 1.0)
                    gradient = 1.0;
                if (gradient < -1.0)
                    gradient = -1.0;

                let cost = (155.4 * (Math.pow(gradient, 5))) - (30.4 * Math.pow(gradient, 4)) - (43.4 * Math.pow(gradient, 3)) - (46.3 * (gradient * gradient)) - (19.5 * gradient) + 3.6;
                pace = pace + (cost - 3.6) / 3.6;

                if (pace < 0.0)
                    pace = 0.0;
            }

            return {"date": new Date(x.date), "value": pace};
        }
        return {"date": new Date(x.date), "value": 0.0};
    });
    return gap_list;
}
