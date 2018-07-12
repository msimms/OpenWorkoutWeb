# Copyright 2017 Michael J Simms
"""Main application, contains all web page handlers"""

import argparse
import cherrypy
import datetime
import json
import logging
import mako
import markdown
import os
import re
import signal
import shutil
import sys
import traceback
import uuid

import StraenApi
import StraenKeys
import DataMgr
import UserMgr

from dateutil.tz import tzlocal
from cherrypy import tools
from cherrypy.process.plugins import Daemonizer
from mako.lookup import TemplateLookup
from mako.template import Template


ACCESS_LOG = 'access.log'
ERROR_LOG = 'error.log'
PRODUCT_NAME = 'Straen'

UNNAMED_ACTIVITY_TITLE = "Unnamed"
UNSPECIFIED_ACTIVITY_TYPE = "Unknown"

LOGIN_URL = '/login'
DEFAULT_LOGGED_IN_URL = '/all_activities'
HTML_DIR = 'html'

g_root_dir = os.path.dirname(os.path.abspath(__file__))
g_root_url = 'http://straen-app.com'
g_tempfile_dir = os.path.join(g_root_dir, 'tempfile')
g_tempmod_dir = os.path.join(g_root_dir, 'tempmod')
g_map_single_html_file = os.path.join(g_root_dir, HTML_DIR, 'map_single_google.html')
g_map_multi_html_file = os.path.join(g_root_dir, HTML_DIR, 'map_multi_google.html')
g_error_logged_in_html_file = os.path.join(g_root_dir, HTML_DIR, 'error_logged_in.html')
g_app = None
g_google_maps_key = ""


def signal_handler(signal, frame):
    global g_app

    print "Exiting..."
    if g_app is not None:
        g_app.terminate()
    sys.exit(0)


@cherrypy.tools.register('before_finalize', priority=60)
def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"


def check_auth(*args, **kwargs):
    global g_app

    # A tool that looks in config for 'auth.require'. If found and it is not None, a login
    # is required and the entry is evaluated as a list of conditions that the user must fulfill
    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions is not None:
        requested_url = cherrypy.request.request_line.split()[1]
        requested_url_parts = requested_url.split('/')
        requested_url_parts = filter(lambda part: part != '', requested_url_parts)

        # If the user is trying to view an activity then make sure they have permissions
        # to view it. First check to see if it's a public activity.
        if requested_url_parts[0] == "device":
            url_params = requested_url_parts[1].split("?")
            if url_params is not None and len(url_params) >= 2:
                device = url_params[0]
                activity_params = url_params[1].split("=")
                if activity_params is not None and len(activity_params) >= 2:
                    activity_id_str = activity_params[1]
                    if g_app.activity_is_public(device, activity_id_str):
                        return

        username = g_app.user_mgr.get_logged_in_user()
        if username:
            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    raise cherrypy.HTTPRedirect(LOGIN_URL)
        else:
            raise cherrypy.HTTPRedirect(LOGIN_URL)


def require(*conditions):
    # A decorator that appends conditions to the auth.require config variable.
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


class StraenWeb(object):
    """Class containing the URL handlers."""

    def __init__(self, user_mgr, data_mgr):
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        super(StraenWeb, self).__init__()

    def terminate(self):
        """Destructor"""
        print "Terminating"
        self.user_mgr.terminate()
        self.user_mgr = None
        self.data_mgr.terminate()
        self.data_mgr = None

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.debug(log_str)

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def update_track(self, activity_id_str=None, num=None, *args, **kw):
        if activity_id_str is None:
            return ""
        if num is None:
            return ""

        try:
            locations = self.data_mgr.retrieve_most_recent_locations(activity_id_str, int(num))

            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            for location in locations:
                if len(response) > 1:
                    response += ","
                response += json.dumps({"latitude": location.latitude, "longitude": location.longitude})

            response += "]"

            return response
        except:
            pass
        return ""

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def update_metadata(self, activity_id_str=None, *args, **kw):
        if activity_id_str is None:
            return ""

        try:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            names = self.data_mgr.retrieve_metadata(StraenKeys.APP_NAME_KEY, activity_id_str)
            if names != None and len(names) > 0:
                response += json.dumps({"name": StraenKeys.APP_NAME_KEY, "value": names[-1][1]})

            times = self.data_mgr.retrieve_metadata(StraenKeys.APP_TIME_KEY, activity_id_str)
            if times != None and len(times) > 0:
                if len(response) > 1:
                    response += ","
                localtimezone = tzlocal()
                value_str = datetime.datetime.fromtimestamp(times[-1][1] / 1000, localtimezone).strftime('%Y-%m-%d %H:%M:%S')
                response += json.dumps({"name": StraenKeys.APP_TIME_KEY, "value": value_str})

            distances = self.data_mgr.retrieve_metadata(StraenKeys.APP_DISTANCE_KEY, activity_id_str)
            if distances != None and len(distances) > 0:
                if len(response) > 1:
                    response += ","
                distance = distances[len(distances) - 1]
                value = float(distance.values()[0])
                response += json.dumps({"name": StraenKeys.APP_DISTANCE_KEY, "value": "{:.2f}".format(value)})

            avg_speeds = self.data_mgr.retrieve_metadata(StraenKeys.APP_AVG_SPEED_KEY, activity_id_str)
            if avg_speeds != None and len(avg_speeds) > 0:
                if len(response) > 1:
                    response += ","
                speed = avg_speeds[len(avg_speeds) - 1]
                value = float(speed.values()[0])
                response += json.dumps({"name": StraenKeys.APP_AVG_SPEED_KEY, "value": "{:.2f}".format(value)})

            moving_speeds = self.data_mgr.retrieve_metadata(StraenKeys.APP_MOVING_SPEED_KEY, activity_id_str)
            if moving_speeds != None and len(moving_speeds) > 0:
                if len(response) > 1:
                    response += ","
                speed = moving_speeds[len(moving_speeds) - 1]
                value = float(speed.values()[0])
                response += json.dumps({"name": StraenKeys.APP_MOVING_SPEED_KEY, "value": "{:.2f}".format(value)})

            heart_rates = self.data_mgr.retrieve_sensordata(StraenKeys.APP_HEART_RATE_KEY, activity_id_str)
            if heart_rates != None and len(heart_rates) > 0:
                if len(response) > 1:
                    response += ","
                heart_rate = heart_rates[len(heart_rates) - 1]
                value = float(heart_rate.values()[0])
                response += json.dumps({"name": StraenKeys.APP_HEART_RATE_KEY, "value": "{:.2f} bpm".format(value)})

            cadences = self.data_mgr.retrieve_sensordata(StraenKeys.APP_CADENCE_KEY, activity_id_str)
            if cadences != None and len(cadences) > 0:
                if len(response) > 1:
                    response += ","
                cadence = cadences[len(cadences) - 1]
                value = float(cadence.values()[0])
                response += json.dumps({"name": StraenKeys.APP_CADENCE_KEY, "value": "{:.2f}".format(value)})

            powers = self.data_mgr.retrieve_sensordata(StraenKeys.APP_POWER_KEY, activity_id_str)
            if powers != None and len(powers) > 0:
                if len(response) > 1:
                    response += ","
                power = powers[len(powers) - 1]
                value = float(power.values()[0])
                response += json.dumps({"name": StraenKeys.APP_POWER_KEY, "value": "{:.2f} watts".format(value)})

            response += "]"

            return response
        except:
            self.log_error('Unhandled exception in update_metadata')
        return ""

    @staticmethod
    def timestamp_format():
        """The user's desired timestamp format."""
        return "%Y/%m/%d %H:%M:%S"

    @staticmethod
    def timestamp_code_to_str(ts_code):
        """Converts from unix timestamp to human-readable"""
        try:
            return datetime.datetime.fromtimestamp(ts_code).strftime(StraenWeb.timestamp_format())
        except:
            pass
        return "-"

    @staticmethod
    def create_navbar(logged_in):
        """Helper function for building the navigation bar."""
        navbar_str = "<nav>\n\t<ul>\n"
        if logged_in:
            navbar_str += \
                "\t\t<li><a href=\"" + g_root_url + "/my_activities/\">My Activities</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/all_activities/\">All Activities</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/following/\">Following</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/followers/\">Followers</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/device_list/\">Devices</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/import_activity/\">Import</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/settings/\">Settings</a></li>\n" \
                "\t\t<li><a href=\"" + g_root_url + "/logout/\">Log Out</a></li>\n"
        else:
            navbar_str += "\t\t<li><a href=\"" + g_root_url + "/login/\">Log In</a></li>\n"
        navbar_str += "\t</ul>\n</nav>"
        return navbar_str

    def render_page_for_activity(self, email, user_realname, activity_id_str, logged_in, is_live):
        """Helper function for rendering the map corresonding to a specific device and activity."""

        locations = self.data_mgr.retrieve_locations(activity_id_str)
        if locations is None or len(locations) == 0:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=g_root_url, error="There is no data for the specified device.")

        route = ""
        center_lat = 0
        center_lon = 0
        last_lat = 0
        last_lon = 0
        max_speed = 0.0
        max_heart_rate = 0.0
        max_cadence = 0.0
        max_power = 0.0

        for location in locations:
            route += "\t\t\t\tnewCoord(" + str(location[StraenKeys.LOCATION_LAT_KEY]) + ", " + str(location[StraenKeys.LOCATION_LON_KEY]) + "),\n"
            last_loc = location

        if len(locations) > 0:
            first_loc = locations[0]
            center_lat = first_loc[StraenKeys.LOCATION_LAT_KEY]
            center_lon = first_loc[StraenKeys.LOCATION_LON_KEY]
            last_lat = last_loc[StraenKeys.LOCATION_LAT_KEY]
            last_lon = last_loc[StraenKeys.LOCATION_LON_KEY]

        current_speeds = self.data_mgr.retrieve_metadata(StraenKeys.APP_CURRENT_SPEED_KEY, activity_id_str)
        current_speeds_str = ""
        if current_speeds is not None and isinstance(current_speeds, list):
            for current_speed in current_speeds:
                time = current_speed.keys()[0]
                value = float(current_speed.values()[0])
                current_speeds_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"
                if value > max_speed:
                    max_speed = value

        heart_rates = self.data_mgr.retrieve_sensordata(StraenKeys.APP_HEART_RATE_KEY, activity_id_str)
        heart_rates_str = ""
        if heart_rates is not None and isinstance(heart_rates, list):
            for heart_rate in heart_rates:
                time = heart_rate.keys()[0]
                value = float(heart_rate.values()[0])
                heart_rates_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"
                if value > max_heart_rate:
                    max_heart_rate = value

        cadences = self.data_mgr.retrieve_sensordata(StraenKeys.APP_CADENCE_KEY, activity_id_str)
        cadences_str = ""
        if cadences is not None and isinstance(cadences, list):
            for cadence in cadences:
                time = cadence.keys()[0]
                value = float(cadence.values()[0])
                cadences_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"
                if value > max_cadence:
                    max_cadence = value

        powers = self.data_mgr.retrieve_sensordata(StraenKeys.APP_POWER_KEY, activity_id_str)
        powers_str = ""
        if powers is not None and isinstance(powers, list):
            for power in powers:
                time = power.keys()[0]
                value = float(power.values()[0])
                powers_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"
                if value > max_power:
                    max_power = value

        # Build the summary data view.
        summary = "<ul>\n"
        activity_type = self.data_mgr.retrieve_metadata(StraenKeys.ACTIVITY_TYPE_KEY, activity_id_str)
        if activity_type is None:
            activity_type = UNSPECIFIED_ACTIVITY_TYPE
        summary += "\t<li>Activity Type: " + activity_type + "</li>\n"
        name = self.data_mgr.retrieve_metadata(StraenKeys.APP_NAME_KEY, activity_id_str)
        if name is None:
            name = UNNAMED_ACTIVITY_TITLE
        summary += "\t<li>Name: " + name + "</li>\n"
        avg_speed = self.data_mgr.retrieve_metadata(StraenKeys.APP_AVG_SPEED_KEY, activity_id_str)
        if avg_speed is not None:
            summary += "\t<li>Avg. Speed: {:.2f}</li>\n".format(avg_speed)
        if max_speed > 1:
            summary += "\t<li>Max. Speed: {:.2f}</li>\n".format(max_speed)
        if max_heart_rate > 1:
            summary += "\t<li>Max. Heart Rate: {:.2f}</li>\n".format(max_heart_rate)
        if max_cadence:
            summary += "\t<li>Max. Cadence: {:.2f}</li>\n".format(max_cadence)
        if max_power:
            summary += "\t<li>Max. Power: {:.2f}</li>\n".format(max_power)
        summary += "</ul>\n"

        if is_live:
            page_title = "Live Tracking"
        else:
            page_title = "Activity"

        my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=g_root_url, email=email, name=user_realname, pagetitle=page_title, summary=summary, googleMapsKey=g_google_maps_key, centerLat=center_lat, lastLat=last_lat, lastLon=last_lon, centerLon=center_lon, route=route, routeLen=len(locations), activityId=activity_id_str, currentSpeeds=current_speeds_str, heartRates=heart_rates_str, powers=powers_str)

    def render_page_for_multiple_devices(self, email, user_realname, device_strs, user_id, logged_in):
        """Helper function for rendering the map corresonding to a multiple devices."""

        if device_strs is None:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=g_root_url, error="No device IDs were specified.")

        route_coordinates = ""
        center_lat = 0
        center_lon = 0
        last_lat = 0
        last_lon = 0
        device_index = 0

        for device_str in device_strs:
            activity_id_str = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            if activity_id_str is None:
                continue

            locations = self.data_mgr.retrieve_locations(activity_id_str)
            if locations is None:
                continue

            route_coordinates += "\t\t\tvar routeCoordinates" + str(device_index) + " = \n\t\t\t[\n"
            for location in locations:
                route_coordinates += "\t\t\t\tnewCoord(" + str(location[StraenKeys.LOCATION_LAT_KEY]) + ", " + str(location[StraenKeys.LOCATION_LON_KEY]) + "),\n"
                last_loc = location
            route_coordinates += "\t\t\t];\n"
            route_coordinates += "\t\t\taddRoute(routeCoordinates" + str(device_index) + ");\n\n"

            if len(locations) > 0:
                first_loc = locations[0]
                center_lat = first_loc[StraenKeys.LOCATION_LAT_KEY]
                center_lon = first_loc[StraenKeys.LOCATION_LON_KEY]
                last_lat = last_loc[StraenKeys.LOCATION_LAT_KEY]
                last_lon = last_loc[StraenKeys.LOCATION_LON_KEY]

        my_template = Template(filename=g_map_multi_html_file, module_directory=g_tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=g_root_url, email=email, name=user_realname, googleMapsKey=g_google_maps_key, centerLat=center_lat, centerLon=center_lon, lastLat=last_lat, lastLon=last_lon, routeCoordinates=route_coordinates, routeLen=len(locations), userId=str(user_id))

    @staticmethod
    def render_activity_row(activity, row_id, show_my_options):
        """Helper function for creating a table row describing an activity."""

        # User's real name.
        if StraenKeys.REALNAME_KEY in activity:
            user_realname = activity[StraenKeys.REALNAME_KEY]
        else:
            user_realname = None

        # Activity ID
        if StraenKeys.ACTIVITY_ID_KEY in activity:
            activity_id_str = activity[StraenKeys.ACTIVITY_ID_KEY]
        else:
            return None
        if activity_id_str is None or len(activity_id_str) == 0:
            return None

        # Activity type
        if StraenKeys.ACTIVITY_TYPE_KEY in activity and len(activity[StraenKeys.ACTIVITY_TYPE_KEY]) > 0:
            activity_type = "<b>" + activity[StraenKeys.ACTIVITY_TYPE_KEY] + "</b>"
        else:
            activity_type = "<b>" + UNSPECIFIED_ACTIVITY_TYPE + "</b>"

        # Activity name
        if StraenKeys.ACTIVITY_NAME_KEY in activity and len(activity[StraenKeys.ACTIVITY_NAME_KEY]) > 0:
            activity_name = "<b>" + activity[StraenKeys.ACTIVITY_NAME_KEY] + "</b>"
        else:
            activity_name = "<b>" + UNNAMED_ACTIVITY_TITLE + "</b>"

        # Activity time
        activity_time = "-"
        if StraenKeys.ACTIVITY_TIME_KEY in activity:
            activity_time = "<script>document.write(unix_time_to_local_string(" + str(activity[StraenKeys.ACTIVITY_TIME_KEY]) + "))</script>"

        # Activity visibility
        checkbox_value = "checked"
        checkbox_label = "Public"
        if StraenKeys.ACTIVITY_VISIBILITY_KEY in activity:
            if activity[StraenKeys.ACTIVITY_VISIBILITY_KEY] == "private":
                checkbox_value = "unchecked"
                checkbox_label = "Private"

        row  = "<td>"
        row += activity_type
        row += "</td>"
        row += "<td>"
        row += activity_time
        row += "</td>"
        row += "<td>"
        if user_realname is not None:
            row += user_realname
            row += "<br>"
        row += "<a href=\"" + g_root_url + "/activity/" + activity_id_str + "\">"
        row += activity_name
        row += "</a></td>"
        row += "<td>"
        if show_my_options:
            row += "<input type=\"checkbox\" value=\"\" " + checkbox_value + " id=\"" + str(row_id) + "\" onclick=\"handleVisibilityClick(this, '" + activity_id_str + "')\";>"
            row += "<span>" + checkbox_label + "</span></label>"
            row += "</td>"
            row += "<td>"
            row += "<button type=\"button\" onclick=\"return on_delete('" + activity_id_str + "')\">Delete</button>"
            row += "</td>"
        row += "<tr>"
        return row

    @staticmethod
    def render_user_row(user):
        """Helper function for creating a table row describing a user."""
        row = "<tr>"
        row += "<td>"
        row += user[StraenKeys.USERNAME_KEY]
        row += "</td>"
        row += "<td>"
        row += user[StraenKeys.REALNAME_KEY]
        row += "</td>"
        row += "</tr>\n"
        return row

    def activity_is_public(self, device_str, activity_id_str):
        """Returns TRUE if the logged in user is allowed to view the specified activity."""
        visibility = self.data_mgr.retrieve_activity_visibility(device_str, activity_id_str)
        if visibility is not None:
            if visibility == "public":
                return True
            elif visibility == "private":
                return False
        return True

    @cherrypy.expose
    def error(self, error_str=None):
        """Renders the errorpage."""
        try:
            cherrypy.response.status = 500
            error_html_file = os.path.join(g_root_dir, HTML_DIR, 'error.html')
            my_template = Template(filename=error_html_file, module_directory=g_tempmod_dir)
            if error_str is None:
                error_str = "Internal Error."
        except:
            pass
        return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error=error_str)

    @cherrypy.expose
    def live(self, device_str):
        """Renders the map page for the current activity from a single device."""
        try:
            activity_id_str = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            if activity_id_str is None:
                return self.error()

            # Get the logged in user.
            logged_in_username = self.user_mgr.get_logged_in_user()

            # Determine who owns the device.
            device_user = self.user_mgr.retrieve_user_from_device(device_str)

            # Render from template.
            return self.render_page_for_activity(device_user[StraenKeys.USERNAME_KEY], device_user[StraenKeys.REALNAME_KEY], activity_id_str, logged_in_username is not None, True)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.live.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def activity(self, activity_id_str, *args, **kw):
        """Renders the map page for an activity."""
        try:
            # Get the logged in user.
            logged_in_username = self.user_mgr.get_logged_in_user()

            # Render from template.
            return self.render_page_for_activity("", "", activity_id_str, logged_in_username is not None, False)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.activity.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def device(self, device_str, *args, **kw):
        """Renders the map page for a single device."""
        try:
            # Get the activity ID being requested. If one is not provided then get the latest activity for the device
            activity_id_str = cherrypy.request.params.get("activity_id")
            if activity_id_str is None:
                activity_id_str = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
                if activity_id_str is None:
                    return self.error()

            # Get the logged in user.
            logged_in_username = self.user_mgr.get_logged_in_user()

            # Determine who owns the device.
            device_user = self.user_mgr.retrieve_user_from_device(device_str)

            # Render from template.
            return self.render_page_for_activity(device_user[StraenKeys.USERNAME_KEY], device_user[StraenKeys.REALNAME_KEY], activity_id_str, logged_in_username is not None, False)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.device.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def my_activities(self, *args, **kw):
        """Renders the list of the specified user's activities."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            activities = self.data_mgr.retrieve_user_activity_list(user_id, user_realname, 0, 25)
            row_id = 0
            activities_list_str = "No activities."
            if activities is not None and isinstance(activities, list):
                if len(activities) > 0:
                    activities_list_str = "<table>\n"
                    for activity in activities:
                        activity_str = self.render_activity_row(activity, row_id, True)
                        if activity_str is not None and len(activity_str) > 0:
                            row_id = row_id + 1
                            activities_list_str += activity_str
                            activities_list_str += "\n"
                    activities_list_str += "</table>\n"

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'my_activities.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activities_list=activities_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.my_activities.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def all_activities(self, *args, **kw):
        """Renders the list of all activities the specified user is allowed to view."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            activities = self.data_mgr.retrieve_all_activities_visible_to_user(user_id, user_realname, 0, 25)
            row_id = 0
            activities_list_str = "No activities."
            if activities is not None and isinstance(activities, list):
                if len(activities) > 0:
                    activities_list_str = "<table>\n"
                    for activity in activities:
                        activity_str = self.render_activity_row(activity, row_id, False)
                        if activity_str is not None and len(activity_str) > 0:
                            row_id = row_id + 1
                            activities_list_str += activity_str
                            activities_list_str += "\n"
                    activities_list_str += "</table>\n"

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'all_activities.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activities_list=activities_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.all_activities.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def following(self, *args, **kw):
        """Renders the list of users the specified user is following."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the list of users followed by the logged in user.
            users_following = self.user_mgr.list_users_followed(user_id)
            users_list_str = "Not currently following anyone."
            if users_following is not None and isinstance(users_following, list):
                if len(users_following) > 0:
                    users_list_str = ""
                    for user in users_following:
                        users_list_str += self.render_user_row(user)

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'following.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, users_list=users_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.following.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def followers(self, *args, **kw):
        """Renders the list of users that are following the specified user."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the list of users following the logged in user.
            users_followed_by = self.user_mgr.list_followers(user_id)
            users_list_str = "Not currently being followed by anyone."
            if users_followed_by is not None and isinstance(users_followed_by, list):
                if len(users_followed_by) > 0:
                    users_list_str = ""
                    for user in users_followed_by:
                        users_list_str += self.render_user_row(user)

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'followers.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, users_list=users_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.followers.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def device_list(self, *args, **kw):
        """Renders the list of a user's devices."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the list of devices that are associated with the user.
            devices = self.user_mgr.retrieve_user_devices(user_id)

            # Build a list of table rows from the device information.
            device_list_str = ""
            if devices is not None and isinstance(devices, list):
                device_list_str += "<td><b>Unique Identifier</b></td><td><b>Last Heard From</b></td><tr>\n"
                for device in devices:
                    activity = self.data_mgr.retrieve_most_recent_activity_for_device(device)
                    device_list_str += "\t\t<tr>"
                    device_list_str += "<td><a href=\"" + g_root_url + "/device/" + device + "\">"
                    device_list_str += device
                    device_list_str += "</a></td><td>"
                    if activity is not None:
                        device_list_str += "<script>document.write(unix_time_to_local_string(" + str(activity[StraenKeys.ACTIVITY_TIME_KEY]) + "))</script>"
                    device_list_str += "</td></tr>\n"

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'device_list.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, device_list=device_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.device_list.__name__)
        return self.error()

    @cherrypy.expose
    def upload(self, ufile):
        """Processes an upload request."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, _ = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Generate a random name for the local file.
            upload_path = os.path.normpath(g_tempfile_dir)
            uploaded_file_name, uploaded_file_ext = os.path.splitext(ufile.filename)
            local_file_name = os.path.join(upload_path, str(uuid.uuid4()))
            local_file_name = local_file_name + uploaded_file_ext

            # Write the file.
            with open(local_file_name, 'wb') as saved_file:
                while True:
                    data = ufile.file.read(8192)
                    if not data:
                        break
                    saved_file.write(data)

            # Parse the file and store it's contents in the database.
            if not self.data_mgr.import_file(username, local_file_name, uploaded_file_ext):
                self.log_error('Unhandled exception in upload when processing ' + uploaded_file_name)

            # Remove the local file.
            os.remove(local_file_name)

        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.upload.__name__)
        return self.error()

    @cherrypy.expose
    def manual_entry(self, activity_type):
        """Called when the user selects an activity type, indicatig they want to make a manual data entry."""
        try:
            print activity_type
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.manual_entry.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def import_activity(self, *args, **kw):
        """Renders the import page."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Build the list options for manual entry.
            activity_type_list = self.data_mgr.retrieve_activity_types()
            activity_type_list_str = "\t\t\t<option value=\"-\">-</option>\n"
            for activity_type in activity_type_list:
                activity_type_list_str += "\t\t\t<option value=\"" + activity_type + "\">" + activity_type + "</option>\n"

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'import.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activity_type_list=activity_type_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.import_activity.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def settings(self, *args, **kw):
        """Renders the user's settings page."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)
            if user_id is None:
                self.log_error('Unknown user ID')
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the current settings.
            selected_default_privacy = self.user_mgr.retrieve_user_setting(user_id, StraenKeys.DEFAULT_PRIVACY)

            # Render the alcohol units option.
            privacy_options = "\t\t<option value=\"Public\""
            if selected_default_privacy == StraenKeys.ACTIVITY_VISIBILITY_PUBLIC:
                privacy_options += " selected"
            privacy_options += ">Public</option>\n"
            privacy_options += "\t\t<option value=\"Private\""
            if selected_default_privacy == StraenKeys.ACTIVITY_VISIBILITY_PRIVATE:
                privacy_options += " selected"
            privacy_options += ">Private</option>"

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'settings.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, privacy_options=privacy_options)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.settings.__name__)
        return self.error()

    @cherrypy.expose
    def submit_login(self, *args, **kw):
        """Processes a login."""
        try:
            email = cherrypy.request.params.get("email")
            password = cherrypy.request.params.get("password")

            if email is None or password is None:
                raise Exception("An email address and password were not provided.")
            else:
                if self.user_mgr.authenticate_user(email, password):
                    self.user_mgr.create_new_session(email)
                    raise cherrypy.HTTPRedirect(DEFAULT_LOGGED_IN_URL)
                else:
                    raise Exception("Unknown error.")
        except cherrypy.HTTPRedirect as e:
            raise e
        except Exception as e:
            error_msg = 'Unable to authenticate the user. ' + str(e.args[0])
            self.log_error(error_msg)
            return self.error(error_msg)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.submit_login.__name__)
        return self.error()

    @cherrypy.expose
    def submit_new_login(self, email, realname, password1, password2, *args, **kw):
        """Creates a new login."""
        try:
            if self.user_mgr.create_user(email, realname, password1, password2, ""):
                self.user_mgr.create_new_session(email)
                raise cherrypy.HTTPRedirect(DEFAULT_LOGGED_IN_URL)
            else:
                raise Exception("Unknown error.")
        except cherrypy.HTTPRedirect as e:
            raise e
        except Exception as e:
            error_msg = 'Unable to create the user. ' + str(e.args[0])
            self.log_error(error_msg)
            return self.error(error_msg)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.submit_new_login.__name__)
        return self.error()

    @cherrypy.expose
    def login(self):
        """Renders the login page."""
        try:
            # If a user is already logged in then go straight to the landing page.
            username = self.user_mgr.get_logged_in_user()
            if username is not None:
                raise cherrypy.HTTPRedirect(DEFAULT_LOGGED_IN_URL)

            html = ""
            readme_file_name = os.path.join(g_root_dir, 'README.md')
            with open(readme_file_name, 'r') as readme_file:
                md = readme_file.read()
                extensions = ['extra', 'smarty']
                html = markdown.markdown(md, extensions=extensions, output_format='html5')

            login_html_file = os.path.join(g_root_dir, HTML_DIR, 'login.html')
            my_template = Template(filename=login_html_file, module_directory=g_tempmod_dir)
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url, readme=html)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            result = self.error()
        return result

    @cherrypy.expose
    def create_login(self):
        """Renders the create login page."""
        try:
            create_login_html_file = os.path.join(g_root_dir, HTML_DIR, 'create_login.html')
            my_template = Template(filename=create_login_html_file, module_directory=g_tempmod_dir)
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url)
        except:
            result = self.error()
        return result

    @cherrypy.expose
    def logout(self):
        """Ends the logged in session."""
        try:
            # Get the logged in user.
            username = self.user_mgr.get_logged_in_user()
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Clear the session.
            self.user_mgr.clear_session()

            # Send the user back to the login screen.
            raise cherrypy.HTTPRedirect(LOGIN_URL)

        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            result = self.error()
        return result

    @cherrypy.expose
    def about(self):
        """Renders the about page."""
        try:
            about_html_file = os.path.join(g_root_dir, HTML_DIR, 'about.html')
            my_template = Template(filename=about_html_file, module_directory=g_tempmod_dir)
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url)
        except:
            result = self.error()
        return result

    @cherrypy.expose
    def api(self, *args, **kw):
        """Endpoint for API calls."""
        response = ""
        try:
            # Get the logged in user.
            user_id = None
            username = self.user_mgr.get_logged_in_user()
            if username is not None:
                user_id, _, _ = self.user_mgr.retrieve_user(username)

            # Read the post data.
            cl = cherrypy.request.headers['Content-Length']
            raw_body = cherrypy.request.body.read(int(cl))

            # Process the API request.
            if len(args) > 0:
                api_version = args[0]
                if api_version == '1.0':
                    api = StraenApi.StraenApi(self.user_mgr, self.data_mgr, user_id)
                    handled, response = api.handle_api_1_0_request(args[1:], raw_body)
                    if not handled:
                        cherrypy.response.status = 400
                    else:
                        cherrypy.response.status = 200
                else:
                    cherrypy.response.status = 400
            else:
                cherrypy.response.status = 400
        except Exception as e:
            response = str(e.args[0])
            cherrypy.response.status = 500
        except:
            cherrypy.response.status = 500
        return response

    @cherrypy.expose
    def index(self):
        """Renders the index page."""
        return self.login()

def main():
    global g_root_dir
    global g_root_url
    global g_app
    global g_google_maps_key

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False, help="Prevents the app from going into the background", required=False)
    parser.add_argument("--host", default="", help="Host name on which users will access this website", required=False)
    parser.add_argument("--hostport", type=int, default=0, help="Port on which users will access this website", required=False)
    parser.add_argument("--bind", default="127.0.0.1", help="Host name on which to bind", required=False)
    parser.add_argument("--bindport", type=int, default=8080, help="Port on which to bind", required=False)
    parser.add_argument("--https", action="store_true", default=False, help="Runs the app as HTTPS", required=False)
    parser.add_argument("--cert", default="cert.pem", help="Certificate file for HTTPS", required=False)
    parser.add_argument("--privkey", default="privkey.pem", help="Private Key file for HTTPS", required=False)
    parser.add_argument("--googlemapskey", default="", help="API key for Google Maps", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if args.https:
        print "Running HTTPS...."
        cherrypy.server.ssl_module = 'builtin'
        cherrypy.server.ssl_certificate = args.cert
        print "Certificate File: " + args.cert
        cherrypy.server.ssl_private_key = args.privkey
        print "Private Key File: " + args.privkey
        protocol = "https"
    else:
        protocol = "http"

    if len(args.host) == 0:
        if args.debug:
            args.host = "127.0.0.1"
        else:
            args.host = "straen-app.com"
        print "Hostname not provided, will use " + args.host

    g_root_url = protocol + "://" + args.host
    if args.hostport > 0:
        g_root_url = g_root_url + ":" + str(args.hostport)
    print "Root URL is " + g_root_url

    if not args.debug:
        Daemonizer(cherrypy.engine).subscribe()

    signal.signal(signal.SIGINT, signal_handler)
    mako.collection_size = 100
    mako.directories = "templates"

    if not os.path.exists(g_tempfile_dir):
        os.makedirs(g_tempfile_dir)

    user_mgr = UserMgr.UserMgr(g_root_dir)
    data_mgr = DataMgr.DataMgr(g_root_dir)
    g_app = StraenWeb(user_mgr, data_mgr)
    g_google_maps_key = args.googlemapskey

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    cherrypy.tools.straenweb_auth = cherrypy.Tool('before_handler', check_auth)

    conf = {
        '/':
        {
            'tools.staticdir.root': g_root_dir,
            'tools.straenweb_auth.on': True,
            'tools.sessions.on': True,
            'tools.sessions.name': 'straenweb_auth',
            'tools.sessions.timeout': 129600,
            'tools.secureheaders.on': True
        },
        '/css':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'css'
        },
        '/js':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'js'
        },
        '/jquery-timepicker':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'jquery-timepicker'
        },
        '/images':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'images',
        },
        '/media':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'media',
        },
        '/.well-known':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.well-known',
        },
    }

    cherrypy.config.update({
        'server.socket_host': args.bind,
        'server.socket_port': args.bindport,
        'requests.show_tracebacks': False,
        'log.access_file': ACCESS_LOG})

    cherrypy.quickstart(g_app, config=conf)

if __name__ == "__main__":
    main()
