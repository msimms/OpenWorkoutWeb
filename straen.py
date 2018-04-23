# Copyright 2017 Michael J Simms
"""Main application, contains all web page handlers"""

import argparse
import cherrypy
import datetime
import json
import logging
import mako
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
SESSION_KEY = '_straen_username'

LOGIN_URL = '/login'
HTML_DIR = 'html'

g_root_dir = os.path.dirname(os.path.abspath(__file__))
g_root_url = 'http://straen-app.com'
g_tempfile_dir = os.path.join(g_root_dir, 'tempfile')
g_tempmod_dir = os.path.join(g_root_dir, 'tempmod')
g_map_single_html_file = os.path.join(g_root_dir, HTML_DIR, 'map_single.html')
g_error_logged_in_html_file = os.path.join(g_root_dir, HTML_DIR, 'error_logged_in.html')
g_app = None


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
                    activity_id = activity_params[1]
                    if g_app.activity_is_public(device, activity_id):
                        return

        username = cherrypy.session.get(SESSION_KEY)
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

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def update_track(self, device_str=None, activity_id_str=None, num=None, *args, **kw):
        if device_str is None:
            return ""
        if activity_id_str is None:
            return ""
        if num is None:
            return ""

        try:
            activity_id = int(activity_id_str)
            if activity_id == 0:
                return ""

            locations = self.data_mgr.retrieve_most_recent_locations(device_str, activity_id, int(num))

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
    def update_metadata(self, device_str=None, activity_id_str=None, *args, **kw):
        if device_str is None:
            return ""
        if activity_id_str is None:
            return ""

        try:
            activity_id = int(activity_id_str)
            if activity_id == 0:
                return ""

            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            names = self.data_mgr.retrieve_metadata(StraenKeys.NAME_KEY, device_str, activity_id)
            if names != None and len(names) > 0:
                response += json.dumps({"name": StraenKeys.NAME_KEY, "value": names[-1][1]})

            times = self.data_mgr.retrieve_metadata(StraenKeys.TIME_KEY, device_str, activity_id)
            if times != None and len(times) > 0:
                if len(response) > 1:
                    response += ","
                localtimezone = tzlocal()
                value_str = datetime.datetime.fromtimestamp(times[-1][1] / 1000, localtimezone).strftime('%Y-%m-%d %H:%M:%S')
                response += json.dumps({"name": StraenKeys.TIME_KEY, "value": value_str})

            distances = self.data_mgr.retrieve_metadata(StraenKeys.DISTANCE_KEY, device_str, activity_id)
            if distances != None and len(distances) > 0:
                if len(response) > 1:
                    response += ","
                distance = distances[len(distances) - 1]
                value = float(distance.values()[0])
                response += json.dumps({"name": StraenKeys.DISTANCE_KEY, "value": "{:.2f}".format(value)})

            avg_speeds = self.data_mgr.retrieve_metadata(StraenKeys.AVG_SPEED_KEY, device_str, activity_id)
            if avg_speeds != None and len(avg_speeds) > 0:
                if len(response) > 1:
                    response += ","
                speed = avg_speeds[len(avg_speeds) - 1]
                value = float(speed.values()[0])
                response += json.dumps({"name": StraenKeys.AVG_SPEED_KEY, "value": "{:.2f}".format(value)})

            moving_speeds = self.data_mgr.retrieve_metadata(StraenKeys.MOVING_SPEED_KEY, device_str, activity_id)
            if moving_speeds != None and len(moving_speeds) > 0:
                if len(response) > 1:
                    response += ","
                speed = moving_speeds[len(moving_speeds) - 1]
                value = float(speed.values()[0])
                response += json.dumps({"name": StraenKeys.MOVING_SPEED_KEY, "value": "{:.2f}".format(value)})

            heart_rates = self.data_mgr.retrieve_sensordata(StraenKeys.HEART_RATE_KEY, device_str, activity_id)
            if heart_rates != None and len(heart_rates) > 0:
                if len(response) > 1:
                    response += ","
                heart_rate = heart_rates[len(heart_rates) - 1]
                value = float(heart_rate.values()[0])
                response += json.dumps({"name": StraenKeys.HEART_RATE_KEY, "value": "{:.2f} bpm".format(value)})

            cadences = self.data_mgr.retrieve_sensordata(StraenKeys.CADENCE_KEY, device_str, activity_id)
            if cadences != None and len(cadences) > 0:
                if len(response) > 1:
                    response += ","
                cadence = cadences[len(cadences) - 1]
                value = float(cadence.values()[0])
                response += json.dumps({"name": StraenKeys.CADENCE_KEY, "value": "{:.2f}".format(value)})

            powers = self.data_mgr.retrieve_sensordata(StraenKeys.POWER_KEY, device_str, activity_id)
            if powers != None and len(powers) > 0:
                if len(response) > 1:
                    response += ","
                power = powers[len(powers) - 1]
                value = float(power.values()[0])
                response += json.dumps({"name": StraenKeys.POWER_KEY, "value": "{:.2f} watts".format(value)})

            response += "]"

            return response
        except:
            cherrypy.log.error('Unhandled exception in update_metadata', 'EXEC', logging.WARNING)
        return ""

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def login_submit(self, **kw):
        """Login - called from the app."""

        try:
            email = cherrypy.request.json["username"]
            password = cherrypy.request.json["password"]
            device_str = cherrypy.request.json["device"]

            response = "["

            if email is None or password is None:
                response += "\"error\": \"An email address and password were not provided.\""
            else:
                user_logged_in, info_str = self.user_mgr.authenticate_user(email, password)
                if user_logged_in:
                    self.user_mgr.create_user_device(email, device_str)
                else:
                    response += "\"error\": \"" + info_str + "\""

            response += "]"
            return response
        except:
            cherrypy.log.error('Unhandled exception in login_submit', 'EXEC', logging.WARNING)
        return ""

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def create_login_submit(self, **kw):
        """ Creates a new login - called from the app."""

        try:
            email = cherrypy.request.json["username"]
            password1 = cherrypy.request.json["password1"]
            password2 = cherrypy.request.json["password2"]
            realname = cherrypy.request.json["realname"]
            device_str = cherrypy.request.json["device"]

            response = "["
            user_created, info_str = self.user_mgr.create_user(email, realname, password1, password2, device_str)
            if user_created:
                response += "\"error\": \"" + info_str + "\""
            response += "]"
            return response
        except:
            cherrypy.log.error('Unhandled exception in create_login_submit', 'EXEC', logging.WARNING)
        return ""

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def list_users_followed(self, email=None, *args, **kw):
        """Lists users followed by the logged in user - called from the app."""

        if email is None:
            return ""

        try:
            followers = self.user_mgr.list_users_followed(email)

            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            for follower in followers:
                if len(response) > 1:
                    response += ","
                response += json.dumps({"username": follower})

            response += "]"

            return response
        except:
            cherrypy.log.error('Unhandled exception in list_users_followed', 'EXEC', logging.WARNING)
        return ""

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def list_followers(self, email=None, *args, **kw):
        """Lists users following the logged in user - called from the app."""

        if email is None:
            return ""

        try:
            followers = self.user_mgr.retrieve_followers(email)

            cherrypy.response.headers['Content-Type'] = 'application/json'
            response = "["

            for follower in followers:
                if len(response) > 1:
                    response += ","
                response += json.dumps({"username": follower})

            response += "]"

            return response
        except:
            cherrypy.log.error('Unhandled exception in list_followers', 'EXEC', logging.WARNING)
        return ""

    @cherrypy.expose
    def update_visibility(self, device_str, activity_id, visibility):
        if device_str is None:
            pass
        if activity_id is None:
            pass

        try:
            if visibility == "true" or visibility == "True":
                new_visibility = "public"
            else:
                new_visibility = "private"

            self.data_mgr.update_activity_visibility(device_str, int(activity_id), new_visibility)
        except:
            cherrypy.log.error('Unhandled exception in my_activities', 'EXEC', logging.WARNING)

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
    def create_navbar():
        """Helper function for building the navigation bar."""

        navbar_str = "<nav>\n" \
            "\t<ul>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/my_activities/\">My Activities</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/all_activities/\">All Activities</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/following/\">Following</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/followers/\">Followers</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/device_list/\">Devices</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/import_activity/\">Import</a></li>\n" \
            "\t\t<li><a href=\"" + g_root_url + "/settings/\">Settings</a></li>\n" \
            "\t</ul>\n" \
            "</nav>"
        return navbar_str

    def render_page_for_activity(self, email, user_realname, device_str, activity_id):
        """Helper function for rendering the map corresonding to a specific device and activity."""

        if device_str is None:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="There is no data for the specified device.")

        locations = self.data_mgr.retrieve_locations(device_str, activity_id)
        if locations is None or len(locations) == 0:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="There is no data for the specified device.")

        route = ""
        center_lat = 0
        center_lon = 0
        last_lat = 0
        last_lon = 0

        for location in locations:
            route += "\t\t\t\tnewCoord(" + str(location[StraenKeys.LOCATION_LAT_KEY]) + ", " + str(location[StraenKeys.LOCATION_LON_KEY]) + "),\n"
            last_loc = location

        if len(locations) > 0:
            first_loc = locations[0]
            center_lat = first_loc[StraenKeys.LOCATION_LAT_KEY]
            center_lon = first_loc[StraenKeys.LOCATION_LON_KEY]
            last_lat = last_loc[StraenKeys.LOCATION_LAT_KEY]
            last_lon = last_loc[StraenKeys.LOCATION_LON_KEY]

        current_speeds = self.data_mgr.retrieve_metadata(StraenKeys.CURRENT_SPEED_KEY, device_str, activity_id)
        current_speeds_str = ""
        if current_speeds is not None and isinstance(current_speeds, list):
            for current_speed in current_speeds:
                time = current_speed.keys()[0]
                value = current_speed.values()[0]
                current_speeds_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        heart_rates = self.data_mgr.retrieve_sensordata(StraenKeys.HEART_RATE_KEY, device_str, activity_id)
        heart_rates_str = ""
        if heart_rates is not None and isinstance(heart_rates, list):
            for heart_rate in heart_rates:
                time = heart_rate.keys()[0]
                value = heart_rate.values()[0]
                heart_rates_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        cadences = self.data_mgr.retrieve_sensordata(StraenKeys.CADENCE_KEY, device_str, activity_id)
        cadences_str = ""
        if cadences is not None and isinstance(cadences, list):
            for cadence in cadences:
                time = cadence.keys()[0]
                value = cadence.values()[0]
                cadences_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        powers = self.data_mgr.retrieve_sensordata(StraenKeys.POWER_KEY, device_str, activity_id)
        powers_str = ""
        if powers is not None and isinstance(powers, list):
            for power in powers:
                time = power.keys()[0]
                value = power.values()[0]
                powers_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"

        my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
        return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=email, name=user_realname, deviceStr=device_str, centerLat=center_lat, lastLat=last_lat, lastLon=last_lon, centerLon=center_lon, route=route, routeLen=len(locations), activityId=str(activity_id), currentSpeeds=current_speeds_str, heartRates=heart_rates_str, powers=powers_str)

    def render_page_for_multiple_devices(self, email, user_realname, device_strs, user_id):
        """Helper function for rendering the map corresonding to a multiple devices."""

        if device_strs is None:
            my_template = Template(filename=g_error_logged_in_html_file, module_directory=g_tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=g_root_url, error="No device IDs were specified.")

        route_coordinates = ""
        center_lat = 0
        center_lon = 0
        last_lat = 0
        last_lon = 0
        device_index = 0

        for device_str in device_strs:
            activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            if activity_id is None:
                continue
            locations = self.data_mgr.retrieve_locations(device_str, activity_id)
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

        my_template = Template(filename=g_map_single_html_file, module_directory=g_tempmod_dir)
        return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=email, name=user_realname, center_lat=center_lat, center_lon=center_lon, last_lat=last_lat, last_lon=last_lon, route_coordinates=route_coordinates, routeLen=len(locations), user_id=str(user_id))

    def render_activity_row(self, user_realname, activity, row_id):
        """Helper function for creating a table row describing an activity."""

        # Activity name
        activity_id = activity[StraenKeys.ACTIVITY_ID_KEY]
        if StraenKeys.ACTIVITY_NAME_KEY in activity:
            activity_name = activity[StraenKeys.ACTIVITY_NAME_KEY]
        else:
            activity_name = "Untitled"

        # Activity time
        activity_time = "-"
        if StraenKeys.ACTIVITY_TIME_KEY in activity:
            activity_time = self.timestamp_code_to_str(activity[StraenKeys.ACTIVITY_TIME_KEY])
        elif StraenKeys.ACTIVITY_LOCATIONS_KEY in activity:
            locations = activity[StraenKeys.ACTIVITY_LOCATIONS_KEY]
            if len(locations) > 0:
                first_loc = locations[0]
                if StraenKeys.LOCATION_TIME_KEY in first_loc:
                    time_num = first_loc[StraenKeys.LOCATION_TIME_KEY] / 1000
                    activity_time = self.timestamp_code_to_str(time_num)

        # Activity visibility
        checkbox_value = "checked"
        checkbox_label = "Public"
        if StraenKeys.ACTIVITY_VISIBILITY_KEY in activity:
            if activity[StraenKeys.ACTIVITY_VISIBILITY_KEY] == "private":
                checkbox_value = "unchecked"
                checkbox_label = "Private"

        row = "<div>\n"
        row += "<table>"
        row += "<td>"
        row += activity_id
        row += "</td>"
        row += "<td>"
        row += activity_time
        row += "</td>"
        row += "<td>"
        if user_realname is not None:
            row += user_realname
            row += "<br>"
        row += "<a href=\"" + g_root_url + "\\device\\" + activity[StraenKeys.ACTIVITY_DEVICE_STR_KEY] + "?activity_id=" + activity_id + "\">"
        row += activity_name
        row += "</a></td>"
        row += "<td>"
        row += "<input type=\"checkbox\" value=\"\" " + checkbox_value + " id=\"" + \
            str(row_id) + "\" onclick='handleVisibilityClick(this, \"" + activity[StraenKeys.ACTIVITY_DEVICE_STR_KEY] + "\", " + activity_id + ")';>"
        row += "<span>" + checkbox_label + "</span></label>"
        row += "</td>"
        row += "</table>\n"
        row += "</div>\n"
        return row

    @staticmethod
    def render_user_row(user):
        """Helper function for creating a table row describing a user."""

        row = "<tr>"
        row += "<td>"
        row += user
        row += "</td>"
        row += "</tr>\n"
        return row

    def activity_is_public(self, device_str, activity_id):
        """Returns TRUE if the logged in user is allowed to view the specified activity."""

        visibility = self.data_mgr.retrieve_activity_visibility(device_str, activity_id)
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
            activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            if activity_id is None:
                return self.error()

            # Render from template.
            return self.render_page_for_activity("", "", device_str, activity_id)
        except:
            cherrypy.log.error('Unhandled exception in device', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def device(self, device_str, *args, **kw):
        """Renders the map page for a single device."""

        try:
            activity_id_str = cherrypy.request.params.get("activity_id")
            if activity_id_str is None:
                activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            else:
                activity_id = int(activity_id_str)

            if activity_id is None:
                return self.error()

            # Render from template.
            return self.render_page_for_activity("", "", device_str, activity_id)
        except:
            cherrypy.log.error('Unhandled exception in device', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def my_activities(self, *args, **kw):
        """Renders the list of the specified user's activities."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)

            activities = self.data_mgr.retrieve_user_activities(user_id, 0, 10)
            activities_list_str = ""
            row_id = 0
            if activities is not None and isinstance(activities, list):
                for activity in activities:
                    activities_list_str += self.render_activity_row(None, activity, row_id)
                    row_id = row_id + 1

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'my_activities.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activities_list=activities_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in my_activities', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def all_activities(self, *args, **kw):
        """Renders the list of all activities the specified user is allowed to view."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)

            activities = self.data_mgr.retrieve_user_activities(user_id, 0, 10)
            activities_list_str = ""
            row_id = 0
            if activities is not None and isinstance(activities, list):
                for activity in activities:
                    activities_list_str += self.render_activity_row(user_realname, activity, row_id)
                    row_id = row_id + 1

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'all_activities.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, activities_list=activities_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in all_activities', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def following(self, *args, **kw):
        """Renders the list of users the specified user is following."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)

            # Get the list of users followed by the logged in user.
            users_following = self.user_mgr.list_users_followed(user_id)
            users_list_str = ""
            if users_following is not None and isinstance(users_following, list):
                for user in users_following:
                    users_list_str += self.render_user_row(user)

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'following.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, users_list=users_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in following', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def followers(self, *args, **kw):
        """Renders the list of users that are following the specified user."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)

            users_followed_by = self.user_mgr.list_followers(user_id)
            users_list_str = ""
            if users_followed_by is not None and isinstance(users_followed_by, list):
                for user in users_followed_by:
                    users_list_str += self.render_user_row(user)

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'followers.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, users_list=users_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in followers', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def device_list(self, *args, **kw):
        """Renders the list of a user's devices."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, _, user_realname = self.user_mgr.retrieve_user(username)

            devices = self.user_mgr.list_user_devices(user_id)
            device_list_str = ""
            if devices is not None and isinstance(devices, list):
                for device in devices:
                    device_list_str += "<tr>"
                    device_list_str += "<td>"
                    device_list_str += device
                    device_list_str += "\n"
                    device_list_str += "</td>"
                    device_list_str += "</tr>\n"

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'device_list.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname, device_list=device_list_str)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in device_list', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    def upload(self, ufile):
        """Processes an upload request."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
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
                cherrypy.log.error('Unhandled exception in upload when processing ' + uploaded_file_name, 'EXEC', logging.WARNING)

            # Remove the local file.
            os.remove(local_file_name)

        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in upload', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def import_activity(self, *args, **kw):
        """Renders the import page."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'import.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in settings', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def settings(self, *args, **kw):
        """Renders the user's settings page."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            # Get the details of the logged in user.
            user_id, user_hash, user_realname = self.user_mgr.retrieve_user(username)

            # Render from template.
            html_file = os.path.join(g_root_dir, HTML_DIR, 'settings.html')
            my_template = Template(filename=html_file, module_directory=g_tempmod_dir)
            return my_template.render(nav=self.create_navbar(), product=PRODUCT_NAME, root_url=g_root_url, email=username, name=user_realname)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in settings', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def request_to_follow(self, email, target_email, *args, **kw):
        """Renders the page for inviting someone to follow."""

        try:
            # Get the logged in user.
            username = cherrypy.session.get(SESSION_KEY)
            if username is None:
                raise cherrypy.HTTPRedirect(LOGIN_URL)

            if self.user_mgr.request_to_follow(username, target_email):
                result = ""
            else:
                result = self.error("Unable to process the request.")
            return result
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            cherrypy.log.error('Unhandled exception in request_to_follow', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    @require()
    def submit_user_search(self, *args, **kw):
        """Processes a search user request."""

        try:
            user = cherrypy.request.params.get("searchname")
            matched_users = self.user_mgr.retrieve_matched_users(user)
            for matched_user in matched_users:
                pass
        except:
            cherrypy.log.error('Unhandled exception in submit_user_search', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    def submit_login(self, *args, **kw):
        """Processes a login."""

        try:
            email = cherrypy.request.params.get("email")
            password = cherrypy.request.params.get("password")

            if email is None or password is None:
                result = self.error("An email address and password were not provided.")
            else:
                user_logged_in, info_str = self.user_mgr.authenticate_user(email, password)
                if user_logged_in:
                    cherrypy.session.regenerate()
                    cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
                    result = self.all_activities(email, None, None)
                else:
                    error_msg = "Unable to authenticate the user."
                    if len(info_str) > 0:
                        error_msg += " "
                        error_msg += info_str
                    result = self.error(error_msg)
            return result
        except:
            cherrypy.log.error('Unhandled exception in submit_login', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    def submit_new_login(self, email, realname, password1, password2, *args, **kw):
        """Creates a new login."""

        try:
            user_created, info_str = self.user_mgr.create_user(email, realname, password1, password2, "")
            if user_created:
                cherrypy.session.regenerate()
                cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
                result = self.all_activities(email, *args, **kw)
            else:
                error_msg = "Unable to create the user."
                if len(info_str) > 0:
                    error_msg += " "
                    error_msg += info_str
                    result = self.error(error_msg)
            return result
        except:
            cherrypy.log.error('Unhandled exception in submit_new_login', 'EXEC', logging.WARNING)
        return self.error()

    @cherrypy.expose
    def login(self):
        """Renders the login page."""

        try:
            login_html_file = os.path.join(g_root_dir, HTML_DIR, 'login.html')
            my_template = Template(filename=login_html_file, module_directory=g_tempmod_dir)
            result = my_template.render(product=PRODUCT_NAME, root_url=g_root_url)
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

        if len(args) > 0:
            api_version = args[0]
            if api_version == '1.0':
                api = StraenApi.StraenApi()
                api.handle_api_1_0_request(args[1:])

    @cherrypy.expose
    def index(self):
        """Renders the index page."""
        return self.login()


# Parse command line options.
parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", default=False, help="Prevents the app from going into the background", required=False)
parser.add_argument("--port", type=int, default=8080, help="Port on which to listen", required=False)
parser.add_argument("--https", action="store_true", default=False, help="Runs the app as HTTPS", required=False)
parser.add_argument("--cert", default="cert.pem", help="Certificate file for HTTPS", required=False)
parser.add_argument("--privkey", default="privkey.pem", help="Private Key file for HTTPS", required=False)

try:
    args = parser.parse_args()
except IOError as e:
    parser.error(e)
    sys.exit(1)

if args.debug:
    if args.https:
        g_root_url = "https://127.0.0.1:" + str(args.port)
    else:
        g_root_url = "http://127.0.0.1:" + str(args.port)
else:
    if args.https:
        g_root_url = 'https://straen-app.com'
    else:
        g_root_url = 'http://straen-app.com'

    Daemonizer(cherrypy.engine).subscribe()

if args.https:
    print "Running HTTPS...."
    cherrypy.server.ssl_module = 'builtin'
    cherrypy.server.ssl_certificate = args.cert
    print "Certificate File: " + args.cert
    cherrypy.server.ssl_private_key = args.privkey
    print "Private Key File: " + args.privkey

signal.signal(signal.SIGINT, signal_handler)
mako.collection_size = 100
mako.directories = "templates"

if not os.path.exists(g_tempfile_dir):
    os.makedirs(g_tempfile_dir)

user_mgr = UserMgr.UserMgr(g_root_dir)
data_mgr = DataMgr.DataMgr(g_root_dir)
g_app = StraenWeb(user_mgr, data_mgr)

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
    'server.socket_host': '127.0.0.1',
    'server.socket_port': args.port,
    'requests.show_tracebacks': False,
    'log.access_file': ACCESS_LOG,
    'log.error_file': ERROR_LOG})

cherrypy.quickstart(g_app, config=conf)
