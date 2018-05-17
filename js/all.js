// Copyright 2018 Michael J Simms

function unix_time_to_local_string(unix_time)
{
	var date = new Date(unix_time * 1000);
	return date.toString();
}
