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

function create_gear(root_url, gear_type)
{
    let the_url = root_url + "/api/1.0/create_gear";
    let dict = [];
    let result_text = {};
    let add_time_obj = document.getElementById("date_added");
    let add_time = Date.parse(add_time_obj.value);
    let retired_time_obj = document.getElementById("date_retired");
    let retired_time = Date.parse(retired_time_obj.value);
    let name = document.getElementById("name").value;
    let description = document.getElementById("description").value;

    if (!isNaN(add_time))
        add_time = add_time / 1000;
    if (!isNaN(retired_time))
        retired_time = retired_time / 1000;

    dict.push({["type"] : gear_type});
    dict.push({["add_time"] : add_time});
    dict.push({["retire_time"] : retired_time});
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

function update_gear(root_url, gear_type)
{
    let the_url = root_url + "/api/1.0/update_gear";
    let dict = [];
    let result_text = {};
    let add_time_obj = document.getElementById("date_added");
    let add_time = Date.parse(add_time_obj.value);
    let retired_time_obj = document.getElementById("date_retired");
    let retired_time = Date.parse(retired_time_obj.value);
    let name = document.getElementById("name").value;
    let description = document.getElementById("description").value;

    if (!isNaN(add_time))
        add_time = add_time / 1000;
    if (!isNaN(retired_time))
        retired_time = retired_time / 1000;

    dict.push({["type"] : gear_type});
    dict.push({["add_time"] : add_time});
    dict.push({["retire_time"] : retired_time});
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
        let the_url = root_url + "/api/1.0/delete_gear";
        let dict = [];
        let result_text = {};

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
        let the_url = root_url + "/api/1.0/retire_gear";
        let dict = [];
        let result_text = {};

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
