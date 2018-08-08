// Copyright 2018 Michael J Simms

function unix_time_to_local_string(unix_time)
{
	var date = new Date(unix_time * 1000);
	return date.toString();
}

function serialize(list)
{
	var str = [];
    for (var i = 0; i < list.length; ++i)
		for (var key in list[i])
			str.push("\"" + encodeURIComponent(key) + "\": \"" + encodeURIComponent(list[i][key]) + "\"");
	json_str = "{" + str.join(",") + "}"
	return json_str
}

function send_post_request(url, params, result_text)
{
	var result = false;

	var xml_http = new XMLHttpRequest();
	var content_type = "application/json; charset=utf-8";

	xml_http.open("POST", url, false);
	xml_http.setRequestHeader('Content-Type', content_type);

	xml_http.onreadystatechange = function()
	{
		if (xml_http.readyState == XMLHttpRequest.DONE)
		{
			result_text.value = xml_http.responseText;
		}
		result = (xml_http.status == 200);
	}
	xml_http.send(serialize(params));
	return result;
}
