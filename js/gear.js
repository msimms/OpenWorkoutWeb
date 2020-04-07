// Copyright 2020 Michael J Simms

function create_gear(target, gearType)
{
    var the_url = "${root_url}/api/1.0/create_gear";
    var dict = [];
    var result_text = {};
    var innerDiv = document.getElementById("new_gear_div");
    var addTimeObj = new Date(document.getElementById("startDate").value);
    var addTime = addTimeObj.getTime() / 1000;
    var retiredTimeObj = new Date(document.getElementById("retiredDate").value);
    var retiredTime = retiredTimeObj.getTime() / 1000;
    var name = document.getElementById("Name").value;
    var description = document.getElementById("Description").value;

    dict.push({["type"] : gearType});
    dict.push({["add_time"] : addTime});
    dict.push({["retire_time"] : retiredTime});
    dict.push({["name"] : name});
    dict.push({["description"] : description});

    if (send_post_request(the_url, dict, result_text))
    {
        window.location.replace("${root_url}/gear");
    }
    else
    {
        alert(result_text.value);
    }
}

function update_gear(target, gearType)
{
    var the_url = "${root_url}/api/1.0/create_gear";
    var dict = [];
    var result_text = {};
    var innerDiv = document.getElementById("new_gear_div");
    var addTimeObj = new Date(document.getElementById("startDate").value);
    var addTime = addTimeObj.getTime() / 1000;
    var retiredTimeObj = new Date(document.getElementById("retiredDate").value);
    var retiredTime = retiredTimeObj.getTime() / 1000;
    var name = document.getElementById("Name").value;
    var description = document.getElementById("Description").value;

    dict.push({["type"] : gearType});
    dict.push({["add_time"] : addTime});
    dict.push({["retire_time"] : retiredTime});
    dict.push({["name"] : name});
    dict.push({["description"] : description});

    if (send_post_request(the_url, dict, result_text))
    {
        window.location.replace("${root_url}/gear");
    }
    else
    {
        alert(result_text.value);
    }
}

function delete_gear(gear_id)
{
    if (confirm('Are you sure you want to do this?'))
    {
        var the_url = "${root_url}/api/1.0/delete_gear";
        var dict = [];
        var result_text = {};

        dict.push({["gear_id"] : gear_id});

        if (send_post_request(the_url, dict, result_text))
        {
            window.location.replace("${root_url}/gear");
        }
        else
        {
            alert(result_text.value);
        }
    }
}

function get_new_gear_info(gearType)
{
    var outerDiv = document.getElementById("block");
    var innerDiv = document.createElement('div');
    innerDiv.id = "new_gear_div";

    // Remove existing items, if any.
    while (outerDiv.firstChild)
    {
        outerDiv.removeChild(outerDiv.firstChild);
    }

    // Determine which data fields are needed.
    var fields = ["Name", "Description"];

    // Add a label for the date picker.
    var dateLabel = document.createTextNode("Date Added: ");
    innerDiv.appendChild(dateLabel);

    // Add the date picker.
    var today = new Date();
    var startDate = document.createElement('input');
    startDate.type = "input";
    startDate.id = "startDate";
    startDate.className = "pickDate";
    $(startDate).datepicker({showButtonPanel: true, defaultDate: today});
    $(startDate).datepicker('setDate', today);
    innerDiv.appendChild(startDate);

    // Add a line break.
    var br = document.createElement("br");
    innerDiv.appendChild(br);

    // Add a label for the date retired picker.
    var dateLabel = document.createTextNode("Date Retired: ");
    innerDiv.appendChild(dateLabel);

    // Add the date retired picker.
    var retiredDate = document.createElement('input');
    retiredDate.type = "input";
    retiredDate.id = "retiredDate";
    retiredDate.className = "pickDate";
    $(retiredDate).datepicker({showButtonPanel: true});
    innerDiv.appendChild(retiredDate);

    // Add a line break.
    br = document.createElement("br");
    innerDiv.appendChild(br);

    // Add the data fields.
    for (i = 0, len = fields.length; i < len; i++)
    {
        add_text_entry_node(innerDiv, fields[i]);
    }

    // Add to the div.
    outerDiv.appendChild(innerDiv);

    // Create a save button.
    var saveBtn = document.createElement('button');
    var saveBtnText = document.createTextNode('Save');
    saveBtn.appendChild(saveBtnText);
    saveBtn.title = "Save";
    saveBtn.addEventListener('click', function() { create_gear(this, gearType); });

    // Add the save button to the screen.
    outerDiv.appendChild(saveBtn);
}

function get_new_bike_info()
{
    get_new_gear_info("bike");
}

function get_new_shoes_info()
{
    get_new_gear_info("shoes");
}
