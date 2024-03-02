// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2022 Michael J Simms
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

/// @function common_refresh_analysis
function common_refresh_analysis(root_url)
{
    let api_url = root_url + "/api/1.0/refresh_analysis";
    let dict = [];

    dict.push({["activity_id"] : activity_id});

    send_post_request_async(api_url, dict, function(status, response) {
        if (status == 200)
            window.location.reload();
        else
            alert(response)
    });
}

/// @function common_create_comment
function common_create_comment(root_url)
{
    let api_url = root_url + "/api/1.0/create_comment";
    let comment = document.getElementById("comment").value;
    let dict = [];

    dict.push({["activity_id"] : activity_id});
    dict.push({["comment"] : comment});

    send_post_request_async(api_url, dict, function(status, response) {
        if (status == 200)
            window.location.reload();
        else
            alert(response)
    });
}

/// @function common_export_activity
function common_export_activity(root_url)
{
    let api_url = root_url + "/api/1.0/export_activity?activity_id=";
    api_url += activity_id
    api_url += "&export_format="
    api_url += document.getElementById("format").value;
    window.location.replace(api_url);
}

/// @function common_edit_activity
function common_edit_activity(root_url)
{
    let api_url = root_url + "/edit_activity/" + activity_id;
    window.location.assign(api_url);
}

/// @function common_add_photos
function common_add_photos(root_url)
{
    let api_url = root_url + "/add_photos/" + activity_id;
    window.location.assign(api_url);
}

/// @function common_trim_activity
function common_trim_activity(root_url)
{
    let api_url = root_url + "/trim_activity/" + activity_id;
    window.location.assign(api_url);
}

/// @function common_merge_activity
function common_merge_activity(root_url)
{
    let api_url = root_url + "/merge_activity/" + activity_id;
    window.location.assign(api_url);
}

/// @function common_delete_activity
function common_delete_activity(root_url)
{
    if (confirm('Are you sure you want to do this? This cannot be undone.'))
    {
        let api_url = root_url + "/api/1.0/delete_activity";
        let dict = [];

        dict.push({["activity_id"] : activity_id});

        send_post_request_async(api_url, dict, function(status, response) {
            if (status == 200)
                window.location.replace(root_url + "/all_activities/");
            else
                alert(response)
        });
    }
}

/// @function common_delete_photo
function common_delete_photo(root_url, photo_id)
{
    if (confirm('Are you sure you want to delete the above photo?'))
    {
        let api_url = root_url + "/api/1.0/delete_activity_photo?activity_id=" + activity_id + "&photo%20id=" + photo_id;

        send_delete_request_async(api_url, function(status, response) {
            if (status == 200)
                window.location.reload();
            else
                alert(response)
        });
    }
}

/// @function common_list_photos
function common_list_photos(root_url)
{
    let api_url = root_url + "/api/1.0/list_activity_photos?activity_id=" + activity_id;

    send_get_request_async(api_url, function (response_code, response_text) {
        if (response_code == 200)
        {
            const records = JSON.parse(response_text);
            process_photos_list(records);
        }
    });
}

/// @function common_create_tags
function common_create_tags(root_url, tags)
{
    let api_url = root_url + "/api/1.0/create_tags_on_activity";
    let dict = [];

    dict.push({["activity_id"] : activity_id});
    for (let tag in tags)
    {
        dict.push({["tag" + tag] : tags[tag]});
    }

    send_post_request_async(api_url, dict, function(status, response) {
        if (status != 200)
            alert(response)
    });
}

/// @function common_process_sensordata
function common_process_sensordata(root_url, activity_id, sensordata, is_foot_based_activity, start_time_ms, resting_hr, max_hr, ftp, deletable)
{
    for (key in sensordata)
    {
        let old_data = sensordata[key];
        let new_data = old_data.map(function(e) {
            let new_e = {};

            for (let item in e)
            {
                new_e["date"] = new Date(Number(item));
                new_e["value"] = e[item];
            }
            return new_e;
        });

        if (new_data.length > 1 && start_time_ms == 0)
        {
            start_time_ms = new_data[0].date;
            end_time_ms = new_data[new_data.length-1].date;
        }

        if (key == "Current Speed")
        {
            draw_speed_graph(start_time_ms, end_time_ms, new_data);
        }
        else if (key == "Heart Rate")
        {
            let hr_zones = compute_heart_rate_zone_distribution(resting_hr, max_hr, new_data);

            if (hr_zones.length > 0 && Math.max.apply(Math, hr_zones) > 0)
            {
                graph_name = "Heart Rate Zone Distribution"
                draw_bar_chart(hr_zones, "Heart Rate Zone Distribution", get_graph_color(graph_name));
            }
            draw_graph(root_url, activity_id, start_time_ms, end_time_ms, new_data, key, "BPM", get_graph_color(key), deletable);
        }
        else if (key == "Cadence")
        {
            draw_graph(root_url, activity_id, start_time_ms, end_time_ms, new_data, key, "RPM", get_graph_color(key), deletable);
        }
        else if (key == "Power")
        {
            let power_zones = compute_power_zone_distribution(ftp, new_data);

            if (!is_foot_based_activity)
            {
                if (power_zones.length > 0 && Math.max.apply(Math, power_zones) > 0)
                {
                    graph_name = "Power Zone Distribution"
                    draw_bar_chart(power_zones, "Power Zone Distribution", get_graph_color(graph_name));
                }
            }
            draw_graph(root_url, activity_id, start_time_ms, end_time_ms, new_data, key, "Watts", get_graph_color(key), deletable);
        }
        else if (key == "Temperature")
        {
            draw_graph(root_url, activity_id, start_time_ms, end_time_ms, new_data, key, "Temperature", get_graph_color(key), deletable);
        }
        else if (key == "Threat Count")
        {
            draw_graph(root_url, activity_id, start_time_ms, end_time_ms, new_data, key, "Threat Count", get_graph_color(key), deletable);
        }
        else if (key == "Battery Level")
        {
            draw_graph(root_url, activity_id, start_time_ms, end_time_ms, new_data, key, "Battery Level", get_graph_color(key), deletable);
        }
        else if (key == "Events")
        {
            let events = sensordata[key];
            let total_strokes = [];
            let total_timer_time = [];

            events.forEach((item, index) => {
                let time = item["timestamp"] * 1000;

                if ("event" in item && item["event"] == "length")
                {
                    if ("total_strokes" in item && item["total_strokes"] != null)
                    {
                        total_strokes.push(item["total_strokes"]);
                    }
                    if ("total_timer_time" in item && item["total_timer_time"] != null)
                    {
                        total_timer_time.push({ date: new Date(time), value:item["total_timer_time"] });
                    }
                }
            });

            draw_bar_chart(total_strokes, "Total Strokes", "LightSteelBlue");
            draw_graph(root_url, activity_id, 0, 0, total_timer_time, "Lap Time", "Lap Time", get_graph_color("Lap Time"), false);
        }
        else if (key == "accelerometer")
        {
            let accel_data = sensordata[key];
            let x_data = [];
            let y_data = [];
            let z_data = [];

            accel_data.forEach((item, index) => {
                let time = item["time"];

                x_data.push({ date: new Date(time), value:item["x"] });
                y_data.push({ date: new Date(time), value:item["y"] });
                z_data.push({ date: new Date(time), value:item["z"] });
            });

            draw_simple_graph(x_data, "x", get_graph_color("x"));
            draw_simple_graph(y_data, "y", get_graph_color("y"));
            draw_simple_graph(z_data, "z", get_graph_color("z"));
        }
    }
}

function common_delete_sensor_data(root_url, activity_id, sensor_name)
{
    if (confirm('Are you sure you want to do delete this sensor data? It cannot be undone.'))
    {
        let api_url = root_url + "/api/1.0/delete_sensor_data";
        let dict = [];

        dict.push({["activity_id"] : activity_id});
        dict.push({["sensor_name"] : sensor_name});

        send_post_request_async(api_url, dict, function(status, response) {
            if (status == 200)
                window.location.reload();
            else
                alert(response)
        });
    }
}
