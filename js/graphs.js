// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2020-2025 Michael J Simms
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
function pad(num, size) {
    var s = "000000000" + num;
    return s.substr(s.length - size);
}

/// @function convert_seconds_to_hours_mins_secs
/// Converts seconds to HH:MM:SS format.
function convert_seconds_to_hours_mins_secs(seconds_in) {
    minutes = Math.trunc(seconds_in / 60);
    hours = Math.trunc(minutes / 60);
    minutes = Math.trunc(minutes % 60);
    out_str = pad(hours.toFixed(0), 2) + ":" + pad(minutes.toFixed(0), 2) + ":" + pad(seconds_in.toFixed(0), 2);
    return out_str;
}

/// @function get_graph_color
function get_graph_color(key) {
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

/// Encapsulates graph settings to reduce the number of things we need to pass to the draw functions.
class GraphSettings {
    constructor() {
        this.element_id = "";
        this.label = "";
        this.unit_label = "";
        this.color = "Yellow";
        this.height = 100;
        this.x_axis_label = "secs";
        this.y_axis_labels = [];
        this.fill = false;
        this.num_columns = 1;
    }
}

/// @function draw_graph
/// A function that allows the graph to be updated is returned.
function draw_graph(root_url, activity_id, data, settings, deleteable, column_index = 0) {
    if (data.length <= 1) {
        return;
    }

    let parent = "#charts";
    let parent_width = document.getElementById("charts").offsetWidth;

    let margin = { top: 20, right: 0, bottom: 40, left: 80 };

    let total_width = parent_width - margin.left - margin.right; // usable width
    let column_width = total_width / settings.num_columns; // total divided into columns

    let left = (column_index * column_width) + margin.left;
    let height = settings.height - margin.top - margin.bottom;

    let svg_width = column_width;
    let svg_height = height + margin.top + margin.bottom;

    let tooltip = d3.select("#charts")
        .append("div")
            .attr("id", settings.element_id + "_tooltip")
            .style("opacity", 0)
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("z-index", 1)
            .style("cursor", "pointer")
            .style("background-color", "gray")
            .style("border", "solid")
            .style("border-width", "1px")
            .style("border-radius", "5px")
            .style("padding", "10px")
    let mouseover = function() {
        tooltip
            .style("opacity", 0.75)
            .style("visibility", "visible")
    }
    let mousemove = function() {
        let coordinates = d3.mouse(this);
        let x = Math.floor((coordinates[0] / column_width) * data.length);

        if (x >= 0 && x < data.length) {
            let value = data[x].y;
            var y_str = "";

            if (typeof value == "string") {
                y_str = value;
            }
            else if (typeof value == "number") {
                y_str = value.toFixed(2);
            }

            if (y_str.length > 0) {
                tooltip
                    .html("<b>" + convert_seconds_to_hours_mins_secs(data[x].x) + " " + settings.x_axis_label + ", " + y_str + " " + settings.unit_label + "</b>")
                    .style("top", (event.pageY) + "px")
                    .style("left", (event.pageX) + "px")
            }
        }
    }
    let mouseleave = function() {
        tooltip
            .style("visibility", "hidden")
    }

    // Set up the SVG.
    var svg = d3.select(parent)
        .append("svg")
            .attr("id", settings.element_id)
            .attr("preserveAspectRatio", "xMinYMin meet")
            .attr("viewBox", "0 0 " + svg_width  + " " + svg_height)
            .attr("width", svg_width)
            .attr("height", svg_height)
            .on('mouseover', mouseover)
            .on('mousemove', mousemove)
            .on('mouseleave', mouseleave)
        .append("g")
            .attr("transform", "translate(" + left + "," + margin.top + ")");

    // Root group in plot coords (no scale yet).
    const g = svg.append("g");

    // Add a clipPath: everything out of this area won't be drawn.
    const clip_id = "plot-clip";
    svg.append("defs")
        .append("clipPath")
            .attr("id", clip_id)
            .attr("clipPathUnits", "userSpaceOnUse")
        .append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", column_width)
            .attr("height", height);

    // Create the scatter variable: where both the circles and the brush take place.
    const plot = g.append("g").attr("clip-path", `url(#${clip_id})`);

    // Define the gradient.
    if (settings.fill) {
        var gradient = g
            .append("linearGradient")
                .attr("id", "gradient_" + settings.element_id)
                .attr("y1", height * 0.5)
                .attr("y2", height)
                .attr("x1", "0")
                .attr("x2", "0")
                .attr("gradientUnits", "userSpaceOnUse");
        gradient
            .append("stop")
                .attr("offset", "0")
                .attr("stop-color", settings.color)
                .attr("stop-opacity", 1.0);
        gradient
            .append("stop")
                .attr("offset", "1")
                .attr("stop-color", settings.color)
                .attr("stop-opacity", 0.5);
    }

    // Define scales.
    var max_x = d3.max(data, d => d.x);
    if (max_x < 1.0) {
        max_x = 1.0;
    }
    var x_scale = d3.scaleLinear()
        .domain([0, max_x])
        .range([0, column_width]);

    // If we were given labels then we have a non-numeric graph.
    if (settings.y_axis_labels.length > 0) {
        var y_scale = d3.scaleBand()
            .domain(settings.y_axis_labels)
            .range([height, 0]);
    }
    else {
        var max_y = d3.max(data, d => d.y);
        if (max_y < 1.0) {
            max_y = 1.0;
        }
        var y_scale = d3.scaleLinear()
            .domain([d3.min(data, d => d.y), max_y])
            .range([height, 0]);
    }

    // Define the line.
    var line = d3.line()
        .x(d => x_scale(d.x))
        .y(d => y_scale(d.y));

    // Draw the area under the line.
    if (settings.fill) {
        var area = d3.area()
            .x(d => x_scale(d.x))
            .y0(height)
            .y1(d => y_scale(d.y));
        var area_path = plot.append("path")
            .datum(data)
            .attr('fill', 'url(#gradient_' + settings.element_id + ')')
            .attr("d", area);
    }
    else {
        var area_path = plot.append("path")
            .datum(data)
            .attr("stroke", settings.color)
            .attr("stroke-width", 3)
            .attr("d", line)
    }

    // Draw the initial data line.
    if (settings.fill) {
        var line_path = plot.append("path")
            .datum(data)
            .attr("fill", settings.color)
            .attr("stroke", settings.color)
            .attr("stroke-width", 3)
            .attr("d", line)
            .attr("id", "pointline");
    }
    else {
        var line_path = plot.append("path")
            .datum(data)
            .attr("stroke", settings.color)
            .attr("stroke-width", 3)
            .attr("d", line)
            .attr("id", "pointline");
    }

    // Add the grid lines.
    let x_axis_grid = d3.axisBottom(x_scale)
        .tickSize(-height)
        .tickSizeOuter(0)
        .tickFormat(function(d) { return convert_seconds_to_hours_mins_secs(d); } );
    svg.append('g')
        .attr('class', 'x axis-grid')
        .attr('transform', 'translate(0,' + height + ')')
        .call(x_axis_grid);
    var num_y_ticks = 5;
    if (settings.y_axis_labels.length > 0) { 
        num_y_ticks = settings.y_axis_labels.length;
    }
    let y_axis_grid = d3.axisLeft(y_scale)
        .tickSize(-column_width)
        .tickSizeOuter(0)
        .tickFormat('')
        .ticks(num_y_ticks);
    svg.append('g')
        .attr('class', 'y axis-grid')
        .call(y_axis_grid);

    // Add the X axis.
    let x_axis = svg.append("g")
        .attr("class", "x_axis")
        .attr("transform", "translate(0," + height + ")")
        .call(x_axis_grid);

    // Add the title and the X axis label.
    if (settings.label.length > 0) {
        svg.append("text")
            .attr("class", "axis")
            .attr("id", settings.element_id + "_title")
            .attr("transform", "translate(" + (column_width / 2) + "," + (height + margin.top - 4) + ")")
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(settings.label);
    }

    // Add the Y axis.
    let y_axis = svg.append("g")
        .attr("class", "y_axis")
        .call(d3.axisLeft(y_scale));

    // Add the Y axis label.
    if (settings.unit_label.length > 0) {
        svg.append("text")
            .attr("class", "axis")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - (left))
            .attr("x", 0 - (height / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(settings.unit_label);
    }

    // Set the zoom and Pan features: how much you can zoom, on which part, and what to do when there is a zoom.
    var zoom = d3.zoom()
        .scaleExtent([.5, 20])  // This controls how much you can unzoom (x0.5) and zoom (x20)
        .extent([[0, 0], [column_width, height]])
        .on("zoom", rescale_chart);

    // This add an invisible rect on top of the chart area.
    // This rect can recover pointer events: necessary to understand when the user zooms.
    svg.append("rect")
        .attr("width", column_width)
        .attr("height", height)
        .style("fill", "none")
        .style("pointer-events", "all")
        .attr('transform', 'translate(' + left + ',' + margin.top + ')')
        .call(zoom);

    if (deleteable) {
        // Create a div for the Delete button.
        let div_name = "delete_" + settings.label;
        d3.select("#charts")
            .append("div")
                .attr("class", div_name)

        // Create the Delete button.
        let delete_btn = document.createElement("button");
        delete_btn.innerHTML = "Delete " + settings.label + " Data";
        delete_btn.setAttribute("style", "color:red;margin:0px");
        let click_action = "return common_delete_sensor_data(\"" + root_url + "\",\"" + activity_id + "\",\"" + settings.label + "\")";
        delete_btn.setAttribute("onclick", click_action);

        // Append it to the newly created div.
        let delete_div = document.getElementsByClassName(div_name)[0];
        delete_div.appendChild(delete_btn);
    }

    // A function that updates the chart when the user zoom and thus new boundaries are available.
    function rescale_chart() {

        // Rescale the axes.
        var new_x_scale = d3.event.transform.rescaleX(x_scale);
        var new_y_scale = d3.event.transform.rescaleY(y_scale);

        // Update axes with these new boundaries.
        x_axis.call(d3.axisBottom(new_x_scale).tickFormat(function(d) { return convert_seconds_to_hours_mins_secs(d); } ));
        y_axis.call(d3.axisLeft(new_y_scale));

        // Re-render the line using the rescaled axes.
        const zline = d3.line().x(d => new_x_scale(d.x)).y(d => new_y_scale(d.y));
        if (settings.fill) {
            area = d3.area()
                .x(d => new_x_scale(d.x))
                .y0(height)
                .y1(d => new_y_scale(d.y));
            area_path.attr("d", zline)
                .attr('fill', 'url(#gradient_' + settings.element_id + ')')
                .attr("d", area);
        }
        else {
            area_path.attr("d", zline);
            line_path.attr("d", zline);
        }
    }

    // Function to update chart.
    function update(new_data) {

        // Concatenate. Need to do this so that tooltips work.
        data = data.concat(new_data);

        // Re-scale.
        x_scale.domain([0, d3.max(data, d => d.x)]);
        if (settings.y_axis_labels.length == 0) {
            y_scale.domain([d3.min(data, d => d.y), d3.max(data, d => d.y)]);
        }

        // Update the line and area.
        if (settings.fill) {
            plot.select("path")
                .datum(new_data)
                .attr("d", line)
                .attr("d", area)
                .attr("id", "pointline");
        }
        else {
            plot.select("path")
                .datum(new_data)
                .attr("d", line)
                .attr("id", "pointline");
        }

        // Update the axis scales.
        x_axis.call(d3.axisBottom(x_scale));
        y_axis.call(d3.axisLeft(y_scale));
    }
    return update;
}

/// @function draw_accelerometer_graph
/// A simple line graph with x data, a title, and a color.
function draw_accelerometer_graph(data, title, color) {
    data = data.map(function(currentValue, index, array) {
        return {"x": index, "y": currentValue.value};
    });

    var settings = new GraphSettings();
    settings.label = title;
    settings.unit_label = "G";
    settings.color = color;
    settings.height = 250;
    return draw_graph("", "", data, settings, false);
}

/// @function draw_sensor_graph
function draw_sensor_graph(root_url, activity_id, data, title, units, color, deleteable) {
    data = data.map(function(currentValue, index, array) {
        return {"x": index, "y": currentValue.value};
    });

    var settings = new GraphSettings();
    settings.label = title;
    settings.unit_label = units;
    settings.color = color;
    settings.height = 250;
    return draw_graph(root_url, activity_id, data, settings, deleteable);
}

/// @function draw_bar_chart
function draw_bar_chart(data, title, color) {
    if (data.length <= 1) {
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

        if (x < data.length) {
            tooltip
                .html("<b>" + convert_seconds_to_hours_mins_secs(data[x]) + "</b>")
                .style("top", (event.pageY) + "px")
                .style("left", (event.pageX) + "px")
        }
    }
    let mouseleave = function() {
    }

    let parent_width = document.getElementById("charts").offsetWidth;

    let margin = { top: 20, right: 0, bottom: 40, left: 80 },
        width = parent_width - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    let x = d3.scaleBand().domain(d3.range(1, data.length + 1)).range([0, width])
    let y = d3.scaleLinear().domain([0, d3.max(data)]).range([height, 0])

    let y_axis = d3.axisLeft(y).ticks(2);

    let svg = d3.select("#charts")
        .append("svg")
            .attr("width", width)
            .attr("height", height + margin.top + margin.bottom)
            .on('mouseover', mouseover)
            .on('mousemove', mousemove)
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
function draw_intervals_graph(start_time_ms, interval_data) {
    interval_graph = [];

    if (interval_data.length > 0) {
        for (let i in interval_data) {
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
function draw_speed_graph(start_time_ms, end_time_ms, data) {
    let unit_system = "${unit_system}";
    let speed_units = ""
    let pace_units = ""

    if (unit_system == "metric") {
        speed_units = "kph";
        pace_units = "mins/km";
    }
    else {
        speed_units = "mph";
        pace_units = "mins/mile";
    }

    if (is_foot_based_activity) {
        let speed_data = convert_speed_graph_to_display_units(unit_system, data);
        let pace_data = convert_speed_graph_to_pace_graph(unit_system, data);
        let gap_data = compute_grade_adjusted_pace(gradient_curve, pace_data);

        draw_sensor_graph(root_url, activity_id, speed_data, "Speed", speed_units, get_graph_color(key), false);
        draw_sensor_graph(root_url, activity_id, pace_data, "Pace", pace_units, get_graph_color(key), false);
        draw_sensor_graph(root_url, activity_id, gap_data, "Grade Adjusted Pace", pace_units, get_graph_color(key), false);
    }
    else {
        let speed_data = convert_speed_graph_to_display_units(unit_system, data);

        draw_sensor_graph(root_url, activity_id, speed_data, "Speed", speed_units, get_graph_color(key), false);
    }
}

/// @function clear_graphs
function clear_graphs() {
    let svg = d3.select("#charts");
    svg.selectAll("*").remove();
}
