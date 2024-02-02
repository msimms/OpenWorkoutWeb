// -*- coding: utf-8 -*-
//
// MIT License
//
// Copyright (c) 2020-2021 Mike Simms
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

/// @function draw_simple_graph
/// A simple line graph with x data, a title, and a color.
function draw_simple_graph(data, title, color)
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
        let x = coordinates[0];

        if (x < data.length)
        {
            tooltip
                .html("<b>" + data[x].value.toFixed(2) + "</b>")
                .style("top", (event.pageY)+"px")
                .style("left", (event.pageX)+"px")
        }
    }
    let mouseleave = function() {
    }

    let margin = { top: 20, right: 20, bottom: 20, left: 50 },
        width = $("#charts").width() - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    let svg = d3.select("#charts")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .on('mouseover', mousemove)
            .on('mousemove', mouseover)
            .on('mouseleave', mouseleave)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Add X axis --> it is a date format.
    let x = d3.scaleTime()
        .domain(d3.extent(data, function(d) { return d.date; }))
        .range([ 0, width ]);
    let x_axis = svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));

    // Add Y axis.
    let y = d3.scaleLinear()
        .domain(d3.extent(data, function(d) { return d.value; }))
        .range([ height, 0 ]);
    let y_axis = svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y));
    svg.append("text")
        .attr("class", "axis")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - (margin.left))
        .attr("x", 0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text(title);

    // Add a clipPath: everything out of this area won't be drawn.
    let clip = svg.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("width", width)
        .attr("height", height)
        .attr("x", 0)
        .attr("y", 0);

    // Add brushing.
    let brush = d3.brushX()                   // Add the brush feature using the d3.brush function
        .extent( [ [0,0], [width, height] ] ) // initialise the brush area: start at 0,0 and finishes at width,height: it means I select the whole graph area
        .on("end", update_chart)              // Each time the brush selection changes, trigger the 'update_chart' function

    let line = svg.append('g')
        .attr("clip-path", "url(#clip)");

    // Add the line.
    line.append("path")
        .datum(data)
        .attr("class", "line")  // I add the class line to be able to modify this line later on.
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 3)
        .attr("d", d3.line()
            .x(function(d) { return x(d.date) })
            .y(function(d) { return y(d.value) })
        )

    // Add the brushing.
    line.append("g")
        .attr("class", "brush")
        .call(brush);

    // A function that set idle_timeout to null.
    var idle_timeout
    function idled() { idle_timeout = null; }

    // A function that update the chart for given boundaries.
    function update_chart() {

        // What are the selected boundaries?
        extent = d3.event.selection

        // If no selection, back to initial coordinate. Otherwise, update X axis domain.
        if (!extent)
        {
            if (!idle_timeout)
                return idle_timeout = setTimeout(idled, 350); // This allows to wait a little bit
            x.domain([4,8])
        }
        else
        {
            x.domain([ x.invert(extent[0]), x.invert(extent[1]) ]);
            line.select(".brush").call(brush.move, null); // This removes the grey brush area as soon as the selection has been done
        }

        // Update axis and line position
        x_axis.transition().duration(1000).call(d3.axisBottom(x))
        line.select('.line')
            .transition()
            .duration(1000)
            .attr("d", d3.line()
                .x(function(d) { return x(d.date) })
                .y(function(d) { return y(d.value) })
            )
    }

    // If user double click, reinitialize the chart
    svg.on("dblclick",function() {
        x.domain(d3.extent(data, function(d) { return d.date; }))
        x_axis.transition().call(d3.axisBottom(x))
        line.select('.line')
            .transition()
            .attr("d", d3.line()
                .x(function(d) { return x(d.date) })
                .y(function(d) { return y(d.value) })
            )
    });
}

/// @function draw_graph
/// A slightly more complicated line graph than with draw_simple_graph.
/// Graph is filled under the line.
/// graph_start_time_ms and graph_end_time_ms allow new graph data to be appended.
function draw_graph(root_url, activity_id, graph_start_time_ms, graph_end_time_ms, data, title, units, color, deleteable)
{
    if (data.length <= 1)
    {
        return;
    }

    let first_point = data[0];
    let last_point = data[data.length - 1];
    let last_ts = last_point["date"].getTime();

    // If the y axis extents were not provided then calculate them now.
    let min_y = d3.min(data, function(d) { return d.value; }) * 0.9;
    let max_y = d3.max(data, function(d) { return d.value; });

    // Need the graphs to start at zero or the fill will look stupid.
    graph_node = {};
    graph_node["date"] = new Date(first_point["date"] - 1);
    graph_node["value"] = 0.0;
    data.unshift(graph_node);

    // To make all the graphs line up, make sure they have the same start and end time.
    if (graph_start_time_ms > 0)
    {
        graph_node = {};
        graph_node["date"] = new Date(graph_start_time_ms);
        graph_node["value"] = 0.0;
        data.unshift(graph_node);
    }

    // Need the graphs to start at zero or the fill will look stupid.
    graph_node = {};
    graph_node["date"] = new Date(last_ts + 1);
    graph_node["value"] = 0.0;
    data.push(graph_node);

    if (graph_end_time_ms >= last_ts)
    {
        graph_node = {};
        graph_node["date"] = new Date(graph_end_time_ms);
        graph_node["value"] = 0.0;
        data.push(graph_node);
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
        let x = coordinates[0];

        if (x < data.length && units.length > 0)
        {
            tooltip
                .html("<b>" + data[x].value.toFixed(2) + " " + units + "</b>")
                .style("top", (event.pageY)+"px")
                .style("left", (event.pageX)+"px")
        }
    }
    let mouseleave = function() {
    }

    let margin = { top: 20, right: 20, bottom: 20, left: 50 },
        width = $("#charts").width() - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    // Create the x axis scale function, which is in date format.
    let x_scale = d3.scaleTime()
        .domain(d3.extent(data, function(d) { return d.date; }))
        .range([ 0, width ]);

    // Create the y axis.
    let y_scale = d3.scaleLinear()
        .domain([ min_y, max_y ])
        .range([ height, 0 ]);

    let svg = d3.select("#charts")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .on('mouseover', mousemove)
            .on('mousemove', mouseover)
            .on('mouseleave', mouseleave)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Create and add the grid lines.
    let x_axis_grid = d3.axisBottom(x_scale)
        .tickSize(-height)
        .tickSizeOuter(0)
        .tickFormat('')
        .ticks(10);
    svg.append('g')
        .attr('class', 'x axis-grid')
        .attr('transform', 'translate(0,' + height + ')')
        .call(x_axis_grid);
    let y_axis_grid = d3.axisLeft(y_scale)
        .tickSize(-width)
        .tickSizeOuter(0)
        .tickFormat('')
        .ticks(10);
    svg.append('g')
        .attr('class', 'y axis-grid')
        .call(y_axis_grid);

    // Add the x axis.
    let x_axis = svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x_scale));

    // If the user double clicks, re-initialize the chart.
    svg.on("dblclick", function() {
        x_scale.domain(d3.extent(data, function(d) { return d.date; }))
        x_axis.transition().call(d3.axisBottom(x_scale))
        line.select('.line')
            .transition()
            .attr("d", d3.line()
                .x(function(d) { return x_scale(d.date) })
                .y(function(d) { return y_scale(d.value) })
            );
    });

    // Add the title.
    if (title.length > 0)
    {
        svg.append("text")
            .attr("class", "axis")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - (margin.left))
            .attr("x", 0 - (height / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(title);
    }

    // Add a clipPath: everything out of this area won't be drawn.
    let clip = svg.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
            .attr("width", width)
            .attr("height", height)
            .attr("x", 0)
            .attr("y", 0);

    // A function that set idle_time_out to null.
    var idle_time_out = null;
    function idled() { idle_time_out = null; }

    // A function that update the chart for given boundaries.
    function update_chart()
    {
        // What are the selected boundaries?
        let extent = d3.event.selection;

        // If no selection, back to initial coordinate. Otherwise, update x axis domain.
        if (extent)
        {
            x_scale.domain([ x_scale.invert(extent[0]), x_scale.invert(extent[1]) ]);
            line.select(".brush").call(brush.move, null); // This removes the grey brush area as soon as the selection has been done.
        }
        else
        {
            if (!idle_time_out)
                return idle_time_out = setTimeout(idled, 350); // This allows to wait a little bit.
            x_scale.domain([4,8])
        }

        // Update the axis and line position.
        x_axis.transition().duration(1000).call(d3.axisBottom(x_scale));
        line.select('.line')
            .transition()
            .duration(1000)
            .attr("d", d3.line()
                .x(function(d) { return x_scale(d.date) })
                .y(function(d) { return y_scale(d.value) })
            );
    }

    // Add the y axis.
    if (units.length > 0)
    {
        let y_axis = svg.append("g")
            .attr("class", "axis")
            .call(d3.axisLeft(y_scale));
    }

    // Create the line.
    let line = svg.append('g')
        .attr("clip-path", "url(#clip)");

    // Add the line.
    line.append("path")
        .datum(data)
        .attr("class", "line")  // I add the class line to be able to modify this line later on.
        .attr("fill", color)
        .attr("stroke", color)
        .attr("stroke-width", 0.25)
        .attr("d", d3.line()
            .x(function(d) { return x_scale(d.date) })
            .y(function(d) { return y_scale(d.value) })
        );

    // Add the brushing.
    let brush = d3.brushX()                        // Add the brush feature using the d3.brush function.
        .extent( [ [ 0, 0 ], [ width, height ] ] ) // Initialise the brush area: start at 0,0 and finishes at width,height: it means I select the whole graph area.
        .on("end", update_chart)                   // Each time the brush selection changes, trigger the 'update_chart' function.
    line.append("g")
        .attr("class", "brush")
        .call(brush);

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

    return svg;
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
                .style("left",(event.pageX) + "px")
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
function draw_intervals_graph(start_time_ms, end_time_ms, interval_data)
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

        draw_graph(root_url, activity_id, start_time_ms, end_time_ms, interval_graph, "Intervals", "", get_graph_color("Intervals"), false);
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

        draw_graph(root_url, activity_id, start_time_ms, end_time_ms, speed_data, "Speed", speed_units, get_graph_color(key), false);
        draw_graph(root_url, activity_id, start_time_ms, end_time_ms, pace_data, "Pace", pace_units, get_graph_color(key), false);
        draw_graph(root_url, activity_id, loc_start_time_ms, loc_end_time_ms, gap_data, "Grade Adjusted Pace", pace_units, get_graph_color(key), false);
    }
    else
    {
        let speed_data = convert_speed_graph_to_display_units(unit_system, data);

        draw_graph(root_url, activity_id, start_time_ms, end_time_ms, speed_data, "Speed", speed_units, get_graph_color(key), false);
    }
}

/// @function clear_graphs
function clear_graphs()
{
    let svg = d3.select("#charts");
    svg.selectAll("*").remove();
}
