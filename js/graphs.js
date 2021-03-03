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

function draw_graph(data, title, units, color)
{
    if (data.length <= 1)
    {
        return;
    }

    // Need to zero out the first and last points or else the fill will look silly.
    data[0].value = 0.0;
    data[data.length-1].value = 0.0;

    var Tooltip = d3.select("#charts")
        .append("div")
            .style("opacity", 0)
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("background-color", "white")
            .style("z-index", 1)
            .style("cursor", "pointer")
    var mouseover = function() {
        Tooltip
            .style("opacity", 0.7)
            .style("visibility", "visible")
    }
    var mousemove = function() {
        let coordinates = d3.mouse(this);
        let x = coordinates[0];

        Tooltip
            .html("<b>" + data[x].value.toFixed(2) + " " + units + "</b>")
            .style("top", (event.pageY)+"px")
            .style("left",(event.pageX)+"px")
    }
    var mouseleave = function() {
    }

    let margin = { top: 20, right: 20, bottom: 20, left: 50 },
        width = $("#charts").width() - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    let x = d3.time.scale().range([0, width]);
    let y = d3.scale.linear().range([height, 0]);

    let xAxis = d3.svg.axis().scale(x).orient("bottom");
    let yAxis = d3.svg.axis().scale(y).orient("left").ticks(5);

    let valueline = d3.svg.line()
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.value); });

    let svg = d3.select("#charts")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .on('mouseover', mousemove)
            .on('mousemove', mouseover)
            .on('mouseleave', mouseleave)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    x.domain(d3.extent(data, function(d) { return d.date; }));
    y.domain(d3.extent(data, function(d) { return d.value; }));

    svg.append("path")
        .attr("class", "line")
        .attr("d", valueline(data))
        .style("fill", color)
        .style("stroke", "LightSlateGray")
        .style("stroke-width", 1.25);
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text(title);
}

function draw_bar_chart(data, title, color)
{
    let xVals = Array.apply(null, Array(data.length)).map(function (x, i) { return i + 1; } );

    let margin = { top: 20, right: 20, bottom: 55, left: 50 },
        width = $("#charts").width() - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    let x = d3.scale.ordinal().domain(xVals).rangeBands([0, width]);
    let y = d3.scale.linear().domain([0, d3.max(data)]).range([height, 0]);

    let xAxis = d3.svg.axis().scale(x).orient("bottom");
    let yAxis = d3.svg.axis().scale(y).orient("left").ticks(0);

    let svg = d3.select("#charts")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", "-.55em")
        .attr("transform", "rotate(-90)" );
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("dy", ".71em")
        .style("text-anchor", "end");
    svg.append("text")
        .attr("transform", "translate(" + (width/2) + " ," + (height + margin.top + 20) + ")")
        .style("text-anchor", "middle")
        .text(title);
    svg.selectAll("bar")
        .data(data)
        .enter().append("rect")
        .style("fill", color)
        .attr("width", x.rangeBand())
        .attr("height", function(d) { return height - y(d); })
        .attr("x", function(d, i) { return x(i+1); })
        .attr("y", function(d) { return y(d); });
}
