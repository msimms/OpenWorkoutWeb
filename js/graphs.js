// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2020-2021 Michael J Simms
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

/// @function pad
/// Utility function for padding a number with leading zeroes.
function pad(num, size)
{
    var s = "000000000" + num;
    return s.substr(s.length - size);
}

/// @function convert_seconds_to_hours_mins_secs
/// Converts seconds to HH:MM:SS format.
function convert_seconds_to_hours_mins_secs(seconds_in)
{
    minutes = Math.trunc(seconds_in / 60);
    hours = Math.trunc(minutes / 60);
    minutes = Math.trunc(minutes % 60);
    out_str = pad(hours.toFixed(0), 2) + ":" + pad(minutes.toFixed(0), 2) + ":" + pad(seconds_in.toFixed(0), 2);
    return out_str;
}

/// @function get_graph_color
function get_graph_color(key)
{
    if (key == "Speed" || key == "Current Speed")
        return "DodgerBlue";
    if (key == "Pace")
        return "DodgerBlue";
    if (key == "Navy")
        return "Navy";
    if (key == "Cadence")
        return "Tan";
    if (key == "Power Zone Distribution")
        return "DarkGreen";
    if (key == "Power")
        return "ForestGreen";
    if (key == "Heart Rate")
        return "Crimson";
    if (key == "Heart Rate Zone Distribution")
        return "DarkRed";
    if (key == "Altitude")
        return "ForestGreen";
    if (key == "Elevation")
        return "PeachPuff";
    if (key == "Temperature")
        return "FireBrick";
    if (key == "x")
        return "DodgerBlue";
    if (key == "y")
        return "FireBrick";
    if (key == "z")
        return "ForestGreen";
    if (key == "Lap Time")
        return "LightSteelBlue";
    if (key == "Threat Count")
        return "FireBrick";
    if (key == "Battery Level")
        return "FireBrick";
    if (key == "Intervals")
        return "Silver";
    return "Gray";
}

/// @function draw_graph
/// Graph is filled under the line.
function draw_graph(root_url, activity_id, data, title, units, color, deleteable)
{
    if (data.length <= 1)
    {
        return;
    }

    let parent = "#charts";
    let parent_width = document.getElementById("charts").offsetWidth;

    let margin = { top: 20, right: 20, bottom: 40, left: 50 },
        width = parent_width - margin.left - margin.right,
        height = 260 - margin.top - margin.bottom;

    let tooltip = d3.select("#charts")
        .append("div")
            .style("opacity", 0)
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("z-index", 1)
            .style("cursor", "pointer")
    let mouseover = function() {
        tooltip
            .style("opacity", 0.7)
            .style("visibility", "visible")
    }
    let mousemove = function() {
        let coordinates = d3.mouse(this);
        let x = Math.floor((coordinates[0] / width) * data.length);

        if (x < data.length)
        {
            tooltip
                .html("<b>" + data[x].x + " secs = " + data[x].y.toFixed(2) + " " + units + "</b>")
                .style("top", (event.pageY) + "px")
                .style("left", (event.pageX) + "px")
        }
    }
    let mouseleave = function() {
    }

    // Set up the SVG.
    var svg = d3.select(parent)
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .on('mouseover', mousemove)
            .on('mousemove', mouseover)
            .on('mouseleave', mouseleave)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Define scales.
    var x_scale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.x)])
        .range([0, width]);
    var y_scale = d3.scaleLinear()
        .domain([d3.min(data, d => d.y), d3.max(data, d => d.y)])
        .range([height, 0]);

    // Fill the background.
    svg.append("rect")
        .attr("width", width)
        .attr("height", height)
        .attr("fill", "Gainsboro");

    // Draw the area under the line.
    var area = d3.area()
        .x(d => x_scale(d.x))
        .y0(height)
        .y1(d => y_scale(d.y));
    svg.append("path")
        .datum(data)
        .attr("fill", color)
        .attr("d", area);

    // Draw the initial data line.
    var line = d3.line()
        .x(d => x_scale(d.x))
        .y(d => y_scale(d.y));
    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 4)
        .attr("d", line);

    // Add the grid lines.
    let x_axis_grid = d3.axisBottom(x_scale)
        .tickSize(-height)
        .tickSizeOuter(0)
        .tickFormat('')
        .ticks(5);
    let y_axis_grid = d3.axisLeft(y_scale)
        .tickSize(-width)
        .tickSizeOuter(0)
        .tickFormat('')
        .ticks(10);
    svg.append('g')
        .attr('class', 'x axis-grid')
        .attr('transform', 'translate(0,' + height + ')')
        .call(x_axis_grid);
    svg.append('g')
        .attr('class', 'y axis-grid')
        .call(y_axis_grid);

    // Add the X axis.
    let x_axis = svg.append("g")
        .attr("class", "x_axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x_scale));

    // Add the title.
    if (title.length > 0)
    {
        // Add the X axis label.
        svg.append("text")
            .attr("class", "axis")
            .attr("transform", "translate(" + (width / 2) + "," + (height + margin.top) + ")")
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(title);
    }

    // Add the Y axis.
    let y_axis = svg.append("g")
        .attr("class", "y_axis")
        .call(d3.axisLeft(y_scale));

    // Add the Y axis units.
    if (units.length > 0)
    {
        // Add the Y axis label.
        svg.append("text")
            .attr("class", "axis")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - (margin.left))
            .attr("x", 0 - (height / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(units);
    }

    // Function to update chart.
    function update(new_data) {
        data = data.concat(new_data);
        x_scale.domain([0, d3.max(data, d => d.x)]);
        y_scale.domain([d3.min(data, d => d.y), d3.max(data, d => d.y)]);

        // Update the line and area.
        svg.select("path")
            .datum(new_data)
            .attr("d", line)
            .attr("d", area);

        // Update the axis scales.
        svg.select(".y_axis")
            .call(d3.axisLeft(y_scale));
        svg.select(".x_axis")
            .call(d3.axisBottom(x_scale));
    }
    
    if (deleteable)
    {
        // Create a div for the delete button.
        let div_name = "delete_" + title
        d3.select("#charts")
            .append("div")
                .attr("class", div_name)

        // Create the delete button.
        let delete_btn = document.createElement("button");
        delete_btn.innerHTML = "Delete " + title + " Data";
        delete_btn.setAttribute("style", "color:red;margin:0px");
        let click_action = "return common_delete_sensor_data(\"" + root_url + "\",\"" + activity_id + "\",\"" + title + "\")";
        delete_btn.setAttribute("onclick", click_action);

        // Append it to the newly created div.
        let delete_div = document.getElementsByClassName(div_name)[0];
        delete_div.appendChild(delete_btn);
    }

    return update;
}

/// @function draw_accelerometer_graph
/// A simple line graph with x data, a title, and a color.
function draw_accelerometer_graph(data, title, color)
{
    data = data.map(function(currentValue, index, array) {
        return {"x": index, "y": currentValue.value};
    });

    return draw_graph("", "", data, title, "G", color, false);
}

/// @function draw_sensor_graph
function draw_sensor_graph(root_url, activity_id, data, title, units, color, deleteable)
{
    data = data.map(function(currentValue, index, array) {
        return {"x": index, "y": currentValue.value};
    });

    return draw_graph(root_url, activity_id, data, title, units, color, deleteable);
}

/// @function draw_bar_chart
function draw_bar_chart(data, title, color)
{
    if (data.length <= 1)
    {
        return;
    }

    let tooltip = d3.select("#charts")
        .append("div")
            .style("opacity", 0)
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("z-index", 1)
            .style("cursor", "pointer")
    let mouseover = function() {
        tooltip
            .style("opacity", 0.7)
            .style("visibility", "visible")
    }
    let mousemove = function() {
        let coordinates = d3.mouse(this);
        let x = Math.floor((coordinates[0] / width) * data.length);

        if (x < data.length)
        {
            tooltip
                .html("<b>" + convert_seconds_to_hours_mins_secs(data[x]) + "</b>")
                .style("top", (event.pageY) + "px")
                .style("left", (event.pageX) + "px")
        }
    }
    let mouseleave = function() {
    }

    let margin = { top: 20, right: 20, bottom: 55, left: 50 },
        width = $("#charts").width() - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    let x = d3.scaleBand().domain(d3.range(1, data.length + 1)).range([0, width])
    let y = d3.scaleLinear().domain([0, d3.max(data)]).range([height, 0])

    let y_axis = d3.axisLeft(y).ticks(2);

    let svg = d3.select("#charts")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .on('mouseover', mousemove)
            .on('mousemove', mouseover)
            .on('mouseleave', mouseleave)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("text")
        .attr("class", "axis")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - (margin.left))
        .attr("x", 0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text(title);  
    svg.append("g")
        .attr("class", "axis")
        .call(y_axis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("dy", ".71em")
        .style("text-anchor", "end");
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));
    svg.selectAll("bar")
        .data(data)
        .enter().append("rect")
        .style("fill", color)
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return height - y(d); })
        .attr("x", function(d, i) { return x(i+1); })
        .attr("y", function(d) { return y(d); });
}

/// @function draw_intervals_graph
function draw_intervals_graph(start_time_ms, interval_data)
{
    interval_graph = [];

    if (interval_data.length > 0)
    {
        for (let i in interval_data)
        {
            let interval = interval_data[i];
            let start_interval_time = interval[0];
            let end_interval_time = interval[1];

            graph_node = {};
            graph_node["date"] = new Date(start_interval_time - 1000);
            graph_node["value"] = 0;
            interval_graph.push(graph_node);
            graph_node = {};
            graph_node["date"] = new Date(start_interval_time);
            graph_node["value"] = 1;
            interval_graph.push(graph_node);
            graph_node = {};
            graph_node["date"] = new Date(end_interval_time);
            graph_node["value"] = 1;
            interval_graph.push(graph_node);
            graph_node = {};
            graph_node["date"] = new Date(end_interval_time + 1000);
            graph_node["value"] = 0;
            interval_graph.push(graph_node);
        }

        draw_sensor_graph(root_url, activity_id, interval_graph, "Intervals", "", get_graph_color("Intervals"), false);
    }
}

/// @function draw_speed_graph
function draw_speed_graph(start_time_ms, end_time_ms, data)
{
    let unit_system = "${unit_system}";
    let speed_units = ""
    let pace_units = ""

    if (unit_system == "metric")
    {
        speed_units = "kph";
        pace_units = "mins/km";
    }
    else
    {
        speed_units = "mph";
        pace_units = "mins/mile";
    }

    if (is_foot_based_activity)
    {
        let speed_data = convert_speed_graph_to_display_units(unit_system, data);
        let pace_data = convert_speed_graph_to_pace_graph(unit_system, data);
        let gap_data = compute_grade_adjusted_pace(gradient_curve, pace_data);

        draw_sensor_graph(root_url, activity_id, speed_data, "Speed", speed_units, get_graph_color(key), false);
        draw_sensor_graph(root_url, activity_id, pace_data, "Pace", pace_units, get_graph_color(key), false);
        draw_sensor_graph(root_url, activity_id, gap_data, "Grade Adjusted Pace", pace_units, get_graph_color(key), false);
    }
    else
    {
        let speed_data = convert_speed_graph_to_display_units(unit_system, data);

        draw_sensor_graph(root_url, activity_id, speed_data, "Speed", speed_units, get_graph_color(key), false);
    }
}

/// @function clear_graphs
function clear_graphs()
{
    let svg = d3.select("#charts");
    svg.selectAll("*").remove();
}
