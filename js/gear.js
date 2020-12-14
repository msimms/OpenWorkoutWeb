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

function create_gear(root_url, gearType)
{
    var the_url = root_url + "/api/1.0/create_gear";
    var dict = [];
    var result_text = {};
    var add_time_obj = new Date(document.getElementById("startDate").value);
    var add_time = add_time_obj.getTime() / 1000;
    var retired_time_obj = new Date(document.getElementById("retiredDate").value);
    var retiredTime = retired_time_obj.getTime() / 1000;
    var name = document.getElementById("Name").value;
    var description = document.getElementById("Description").value;

    dict.push({["type"] : gearType});
    dict.push({["add_time"] : add_time});
    dict.push({["retire_time"] : retiredTime});
    dict.push({["name"] : name});
    dict.push({["description"] : description});

    if (send_post_request(the_url, dict, result_text))
    {
        window.location.replace(root_url + "/gear");
    }
    else
    {
        alert(result_text.value);
    }
}

function update_gear(root_url, gearType)
{
    var the_url = root_url + "/api/1.0/update_gear";
    var dict = [];
    var result_text = {};
    var add_time_obj = new Date(document.getElementById("startDate").value);
    var add_time = add_time_obj.getTime() / 1000;
    var retired_time_obj = new Date(document.getElementById("retiredDate").value);
    var retiredTime = retired_time_obj.getTime() / 1000;
    var name = document.getElementById("Name").value;
    var description = document.getElementById("Description").value;

    dict.push({["type"] : gearType});
    dict.push({["add_time"] : add_time});
    dict.push({["retire_time"] : retiredTime});
    dict.push({["name"] : name});
    dict.push({["description"] : description});

    if (send_post_request(the_url, dict, result_text))
    {
        window.location.replace(root_url + "/gear");
    }
    else
    {
        alert(result_text.value);
    }
}

function delete_gear(root_url, gear_id)
{
    if (confirm('Are you sure you want to do this?'))
    {
        var the_url = root_url + "/api/1.0/delete_gear";
        var dict = [];
        var result_text = {};

        dict.push({["gear_id"] : gear_id});

        if (send_post_request(the_url, dict, result_text))
        {
            window.location.replace(root_url + "/gear");
        }
        else
        {
            alert(result_text.value);
        }
    }
}

function retire_gear(root_url, gear_id)
{
    if (confirm('Are you sure you want to do this?'))
    {
        var the_url = root_url + "/api/1.0/retire_gear";
        var dict = [];
        var result_text = {};

        dict.push({["gear_id"] : gear_id});

        if (send_post_request(the_url, dict, result_text))
        {
            window.location.replace(root_url + "/gear");
        }
        else
        {
            alert(result_text.value);
        }
    }
}

function get_new_gear_info(root_url, gear_type)
{
    var outer_div = document.getElementById("block");
    var inner_div = document.createElement('div');
    inner_div.id = "new_gear_div";

    // Remove existing items, if any.
    while (outer_div.firstChild)
    {
        outer_div.removeChild(outer_div.firstChild);
    }

    // Determine which data fields are needed.
    var fields = ["Name", "Description"];

    // Add a label for the date picker.
    var date_label = document.createTextNode("Date Added: ");
    inner_div.appendChild(date_label);

    // Add the date picker.
    var today = new Date();
    var start_date = document.createElement('input');
    start_date.type = "input";
    start_date.id = "startDate";
    start_date.className = "pickDate";
    $(start_date).datepicker({showButtonPanel: true, defaultDate: today});
    $(start_date).datepicker('setDate', today);
    inner_div.appendChild(start_date);

    // Add a line break.
    var br = document.createElement("br");
    inner_div.appendChild(br);

    // Add a label for the date retired picker.
    var dateLabel = document.createTextNode("Date Retired: ");
    inner_div.appendChild(dateLabel);

    // Add the date retired picker.
    var retired_date = document.createElement('input');
    retired_date.type = "input";
    retired_date.id = "retiredDate";
    retired_date.className = "pickDate";
    $(retired_date).datepicker({showButtonPanel: true});
    inner_div.appendChild(retired_date);

    // Add a line break.
    br = document.createElement("br");
    inner_div.appendChild(br);

    // Add the data fields.
    for (i = 0, len = fields.length; i < len; i++)
    {
        add_text_entry_node(inner_div, fields[i]);
    }

    // Add to the div.
    outer_div.appendChild(inner_div);

    // Create a save button.
    var save_btn = document.createElement('button');
    var save_btn_text = document.createTextNode('Save');
    save_btn.appendChild(save_btn_text);
    save_btn.title = "Save";
    save_btn.addEventListener('click', function() { create_gear(root_url, gear_type); });

    // Add the save button to the screen.
    outer_div.appendChild(save_btn);
}

function get_new_bike_info(root_url)
{
    get_new_gear_info(root_url, "bike");
}

function get_new_shoes_info(root_url)
{
    get_new_gear_info(root_url, "shoes");
}
