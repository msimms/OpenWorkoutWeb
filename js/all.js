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
			str.push(encodeURIComponent(key) + "=" + encodeURIComponent(list[i][key]));
	return str.join("&");
}

function send_post_request(url, params)
{
	var result = false;

	var xml_http = new XMLHttpRequest();
	var content_type = "application/x-www-form-urlencoded; charset=utf-8";

	xml_http.open("POST", url, false);
	xml_http.setRequestHeader('Content-type', content_type);

	xml_http.onreadystatechange = function()
	{
		result = (xml_http.status == 200);
	}
	xml_http.send(serialize(params));
	return result;
}
