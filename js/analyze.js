// Copyright 2020 Michael J Simms

function degrees_to_radians(degrees)
{
    var pi = Math.PI;
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
    var last_coordinate = null;
    var total_distance_meters = 0.0;

    for (var coordinate of coordinates)
    {
        if (last_coordinate != null)
        {
            var meters_traveled = haversine_distance_ignore_altitude(coordinate.lat(), coordinate.lng(), last_coordinate.lat(), last_coordinate.lng());
            total_distance_meters += meters_traveled;
        }
        last_coordinate = coordinate;
    }
    return total_distance_meters;
}

/// @function Distance calculation for a coordinate array that was built for use with the Open Street Map API.
function total_distance_osm(coordinates)
{
    var last_coordinate = null;
    var total_distance_meters = 0.0;

    for (var coordinate of coordinates)
    {
        last_coordinate = coordinate;
    }
    return total_distance_meters;
}

/// Converts meters to whatever the preferred units are and formats it as a string.
function convert_distance_to_unit_system_str(unit_system, meters_traveled)
{
    if (unit_system == "metric")
    {
        var km = meters_traveled / 1000.0;
        return km.toFixed(2).toString() + " kms";
    }
    miles = meters_traveled * 0.000621371;
    return miles.toFixed(2).toString() + " miles";
}
