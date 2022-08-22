// -*- coding: utf-8 -*-
// 
// MIT License
// 
// Copyright (c) 2022 Mike Simms
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

/// @function refresh_analysis
function common_refresh_analysis(root_url)
{
    let the_url = root_url + "/api/1.0/refresh_analysis";
    let dict = [];
    let result_text = {};

    dict.push({["activity_id"] : activity_id});
    if (send_post_request(the_url, dict, result_text))
        window.location.reload();
    else
        alert(result_text.value);
}

/// @function create_comment
function common_create_comment(root_url)
{
    let the_url = root_url + "/api/1.0/create_comment";
    let comment = document.getElementById("comment").value;
    let dict = [];
    let result_text = {};

    dict.push({["activity_id"] : activity_id});
    dict.push({["comment"] : comment});
    if (send_post_request(the_url, dict, result_text))
        window.location.reload();
    else
        alert(result_text.value);
}

/// @function export_activity
function common_export_activity(root_url)
{
    let the_url = root_url + "/api/1.0/export_activity";
    let format = document.getElementById("format").value;
    let dict = [];
    let result_text = {};

    dict.push({["activity_id"] : activity_id});
    dict.push({["export_format"] : format});
    if (send_post_request(the_url, dict, result_text))
        create_local_file(result_text.value, activity_id + "." + format, "text/plain;charset=utf-8");
    else
        alert(result_text.value);
}

/// @function edit_activity
function common_edit_activity(root_url)
{
    let the_url = root_url + "/edit_activity/" + activity_id;
    window.location.replace(the_url);
}

/// @function add_photos
function common_add_photos(root_url)
{
    let the_url = root_url + "/add_photos/" + activity_id;
    window.location.replace(the_url);
}

/// @function trim_activity
function common_trim_activity(root_url)
{
    let the_url = root_url + "/trim_activity/" + activity_id;
    window.location.replace(the_url);
}

/// @function delete_activity
function common_delete_activity(root_url)
{
    if (confirm('Are you sure you want to do this?'))
    {
        let the_url = root_url + "/api/1.0/delete_activity";
        let dict = [];
        let result_text = {};

        dict.push({["activity_id"] : activity_id});
        if (send_post_request(the_url, dict, result_text))
            window.location.replace(root_url);
        else
            alert(result_text.value);
    }
}

/// @function delete_photo
function common_delete_photo(root_url, photo_id)
{
    if (confirm('Are you sure you want to delete the above photo?'))
    {
        let the_url = root_url + "/api/1.0/delete_activity_photo";
        let dict = [];
        let result_text = {};

        dict.push({["activity_id"] : activity_id});
        dict.push({["photo_id"] : photo_id});
        if (send_post_request(the_url, dict, result_text))
            window.location.reload();
        else
            alert(result_text.value);
    }
}

/// @function list_photos
function common_list_photos(root_url)
{
    let api_url = root_url + "/api/1.0/list_activity_photos?activity_id=" + activity_id;
    $.ajax({ type: 'GET', url: api_url, cache: false, success: process_photos_list, dataType: "json" });
}

/// @function create_tags
function common_create_tags(root_url, tags)
{
    let the_url = root_url + "/api/1.0/create_tags_on_activity";
    let dict = [];
    let result_text = {};

    dict.push({["activity_id"] : activity_id});
    for (let tag in tags)
        dict.push({["tag" + tag] : tags[tag]});
    if (!send_post_request(the_url, dict, result_text))
        alert(result_text.value);
}
