# Copyright 2017-2018 Michael J Simms
"""Main application, contains all web page handlers"""

import cherrypy
import datetime
import json
import logging
import mako
import markdown
import os
import sys
import threading
import time
import timeit
import traceback

import Keys
import LocationAnalyzer
import Api
import BmiCalculator
import DataMgr
import Units
import UserMgr
import VO2MaxCalculator

from dateutil.tz import tzlocal
from mako.lookup import TemplateLookup
from mako.template import Template


PRODUCT_NAME = 'Straen'

LOGIN_URL = '/login'
DEFAULT_LOGGED_IN_URL = '/all_activities'
HTML_DIR = 'html'


g_stats_lock = threading.Lock()
g_stats_count = {}
g_stats_time = {}


def statistics(function):
    """Function decorator for usage and timing statistics."""

    def wrapper(*args, **kwargs):
        global g_stats_lock
        global g_stats_count
        global g_stats_time

        start = timeit.default_timer()
        result = function(*args, **kwargs)
        end = timeit.default_timer()
        execution_time = end - start

        g_stats_lock.acquire()
        try:
            g_stats_count[function.__name__] = g_stats_count[function.__name__] + 1
            g_stats_time[function.__name__] = g_stats_time[function.__name__] + execution_time
        except:
            g_stats_count[function.__name__] = 1
            g_stats_time[function.__name__] = execution_time
        finally:
            g_stats_lock.release()

        return result

    return wrapper


class RedirectException(Exception):
    """This is thrown when the app needs to redirect to another page."""

    def __init__(self, url):
        self.url = url
        super(RedirectException, self).__init__()


class App(object):
    """Class containing the URL handlers."""

    def __init__(self, user_mgr, data_mgr, root_dir, root_url, google_maps_key):
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.root_dir = root_dir
        self.root_url = root_url
        self.tempfile_dir = os.path.join(self.root_dir, 'tempfile')
        self.tempmod_dir = os.path.join(self.root_dir, 'tempmod')
        self.google_maps_key = google_maps_key
        self.lifting_activity_html_file = os.path.join(root_dir, HTML_DIR, 'lifting_activity.html')
        self.map_single_osm_html_file = os.path.join(root_dir, HTML_DIR, 'map_single_osm.html')
        self.map_single_google_html_file = os.path.join(root_dir, HTML_DIR, 'map_single_google.html')
        self.map_multi_html_file = os.path.join(root_dir, HTML_DIR, 'map_multi_google.html')
        self.error_logged_in_html_file = os.path.join(root_dir, HTML_DIR, 'error_logged_in.html')

        self.tempfile_dir = os.path.join(root_dir, 'tempfile')
        if not os.path.exists(self.tempfile_dir):
            os.makedirs(self.tempfile_dir)

        super(App, self).__init__()

    def terminate(self):
        """Destructor"""
        print("Terminating the application...")
        print("Terminating data management...")
        self.data_mgr.terminate()
        self.data_mgr = None
        print("Terminating session management...")
        self.user_mgr.terminate()
        self.user_mgr = None

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

    def stats(self):
        """Renders the list of a user's devices."""
        global g_stats_lock
        global g_stats_count
        global g_stats_time

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Build a list of table rows from the device information.
        page_stats_str = "<td><b>Page</b></td><td><b>Num Accesses</b></td><td><b>Avg Time (secs)</b></td><tr>\n"
        g_stats_lock.acquire()
        try:
            for key, count_value in g_stats_count.iteritems():
                page_stats_str += "\t\t<tr><td>"
                page_stats_str += str(key)
                page_stats_str += "</td><td>"
                page_stats_str += str(count_value)
                page_stats_str += "</td><td>"
                if key in g_stats_time and count_value > 0:
                    total_time = g_stats_time[key]
                    avg_time = total_time / count_value
                    page_stats_str += str(avg_time)
                page_stats_str += "</td></tr>\n"
        finally:
            g_stats_lock.release()

        # The number of users and activities.
        total_users_str = ""
        total_activities_str = ""
        try:
            total_users_str = str(self.data_mgr.total_users_count())
            total_activities_str = str(self.data_mgr.total_activities_count())
        except:
            self.log_error("Exception while getting counts.")

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'stats.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, page_stats=page_stats_str, total_activities=total_activities_str, total_users=total_users_str)

    @staticmethod
    def timestamp_format():
        """The user's desired timestamp format."""
        return "%Y/%m/%d %H:%M:%S"

    @staticmethod
    def timestamp_code_to_str(ts_code):
        """Converts from unix timestamp to human-readable"""
        try:
            return datetime.datetime.fromtimestamp(ts_code).strftime(App.timestamp_format())
        except:
            pass
        return "-"

    def create_navbar(self, logged_in):
        """Helper function for building the navigation bar."""
        navbar_str = "<nav>\n\t<ul>\n"
        if logged_in:
            navbar_str += \
                "\t\t<li><a href=\"" + self.root_url + "/my_activities/\">My Activities</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/all_activities/\">All Activities</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/workouts/\">Workouts</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/gear/\">Gear</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/following/\">Following</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/followers/\">Followers</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/device_list/\">Devices</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/import_activity/\">Import</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/profile/\">Profile</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/settings/\">Settings</a></li>\n" \
                "\t\t<li><a href=\"" + self.root_url + "/logout/\">Log Out</a></li>\n"
        else:
            navbar_str += "\t\t<li><a href=\"" + self.root_url + "/login/\">Log In</a></li>\n"
        navbar_str += "\t</ul>\n</nav>"
        return navbar_str

    def render_tags(self, activity, logged_in):
        """Helper function for building the tags string."""
        activity_tags = []
        if Keys.ACTIVITY_TAGS_KEY in activity:
            activity_tags = activity[Keys.ACTIVITY_TAGS_KEY]
        default_tags = self.data_mgr.list_default_tags()
        all_tags = []
        all_tags.extend(activity_tags)
        all_tags.extend(default_tags)
        all_tags = list(set(all_tags))
        tags_str = ""
        if all_tags is not None:
            for tag in all_tags:
                if tag in activity_tags:
                    tags_str += "<option selected=true>"
                else:
                    tags_str += "<option>"
                tags_str += tag
                tags_str += "</option>\n"
        return tags_str

    def render_gear(self, activity_user_id, activity_type, activity, logged_in):
        """Helper function for building the gear string."""
        if activity_type == Keys.TYPE_RUNNING_KEY or activity_type == Keys.TYPE_HIKING_KEY:
            gear_type = Keys.GEAR_TYPE_SHOES
        elif activity_type == Keys.TYPE_CYCLING_KEY:
            gear_type = Keys.GEAR_TYPE_BIKE
        else:
            return ""

        activity_gear = []
        if Keys.GEAR_KEY in activity:
            activity_gear = activity[Keys.GEAR_KEY]

        all_gear = self.data_mgr.retrieve_gear_of_specified_type_for_user(activity_user_id, gear_type)
        gear_str = ""
        if all_gear is not None:
            for gear in all_gear:
                if Keys.GEAR_NAME_KEY in gear:
                    gear_name = gear[Keys.GEAR_NAME_KEY]
                    if gear_name in activity_gear:
                        gear_str += "<option selected=true>"
                    else:
                        gear_str += "<option>"
                    gear_str += gear_name
                    gear_str += "</option>\n"
        return gear_str

    def render_comments(self, activity, logged_in):
        """Helper function for building the comments string."""
        comments_str = ""
        comments = []
        if Keys.ACTIVITY_COMMENTS_KEY in activity:
            comments = activity[Keys.ACTIVITY_COMMENTS_KEY]
        for comment_entry in comments:
            decoded_entry = json.loads(comment_entry)
            commenter_id = decoded_entry[Keys.ACTIVITY_COMMENTER_ID_KEY]
            _, commenter_name = self.user_mgr.retrieve_user_from_id(commenter_id)
            comments_str += "<td><b>"
            comments_str += commenter_name
            comments_str += "</b> says \""
            comments_str += decoded_entry[Keys.ACTIVITY_COMMENT_KEY]
            comments_str += "\"</td><tr>\n"
        if logged_in:
            comments_str += "<td><textarea rows=\"4\" style=\"width:50%;\" maxlength=\"512\" id=\"comment\"></textarea></td><tr>\n"
            comments_str += "<td><button type=\"button\" onclick=\"return create_comment()\">Post</button></td><tr>\n"
        return comments_str

    def render_export_control(self, logged_in, has_location_data, has_accel_data):
        """Helper function for building the exports string."""
        exports_str = ""
        if logged_in:
            exports_str  = "<td>Export Format:</td><tr>\n"
            exports_str += "<td><select id=\"format\" class=\"checkin\" >\n"
            if has_location_data:
                exports_str += "\t<option value=\"tcx\" selected>TCX</option>\n"
                exports_str += "\t<option value=\"gpx\">GPX</option>\n"
            if has_accel_data:
                exports_str += "\t<option value=\"csv\">CSV</option>\n"
            exports_str += "</select>\n</td><tr>\n"
            exports_str += "<td><button type=\"button\" onclick=\"return export_activity()\">Export</button></td><tr>\n"
        return exports_str

    def render_delete_control(self, logged_in):
        """Helper function for building the delete string."""
        delete_str = ""
        if logged_in:
            delete_str += "<td><button type=\"button\" onclick=\"return delete_activity()\">Delete</button></td><tr>\n"
        return delete_str

    def render_page_for_lifting_activity(self, email, user_realname, activity_id, activity, activity_user_id, logged_in_username, belongs_to_current_user, is_live):
        """Helper function for rendering the map corresonding to a specific device and activity."""

        # Is the user logged in?
        logged_in = logged_in_username is not None

        # Read the accelerometer data (if any).
        accels = []
        if Keys.APP_ACCELEROMETER_KEY in activity:
            accels = activity[Keys.APP_ACCELEROMETER_KEY]

        # Format the accelerometer data.
        x_axis = ""
        y_axis = ""
        z_axis = ""
        for accel in accels:
            time_str = str(accel[Keys.ACCELEROMETER_TIME_KEY])
            x_axis += "\t\t\t\t{ date: new Date(" + time_str + "), value: " + str(accel[Keys.ACCELEROMETER_AXIS_NAME_X]) + " },\n"
            y_axis += "\t\t\t\t{ date: new Date(" + time_str + "), value: " + str(accel[Keys.ACCELEROMETER_AXIS_NAME_Y]) + " },\n"
            z_axis += "\t\t\t\t{ date: new Date(" + time_str + "), value: " + str(accel[Keys.ACCELEROMETER_AXIS_NAME_Z]) + " },\n"

        # Retrieve cached summary data. If summary data has not been computed, then add this activity to the queue and move on without it.
        summary_data = self.data_mgr.retrieve_activity_summary(activity_id)
        if summary_data is None or len(summary_data) == 0:
            self.data_mgr.analyze(activity, activity_user_id)

        # Find the sets data.
        sets = None
        if Keys.APP_SETS_KEY in activity:
            sets = activity[Keys.APP_SETS_KEY]
        elif Keys.APP_SETS_KEY in summary_data:
            sets = summary_data[Keys.APP_SETS_KEY]

        # Build the details view.
        details = ""
        if sets is not None:
            details = "<table>\n<td><b>Set</b></td><td><b>Rep Count</b></td><tr>\n"
            set_num = 1
            for current_set in sets:
                details += "<td>"
                details += str(set_num)
                details += "</td><td>"
                details += str(current_set)
                details += "</td><tr>\n"
                set_num = set_num + 1
            details += "</table>\n"

        # Build the summary data view.
        summary = "<ul>\n"

        # Add the activity type.
        activity_type = self.render_activity_type(activity)
        summary += "\t<li>Activity Type: " + activity_type + "</li>\n"

        # Add the activity date.
        name = self.render_activity_name(activity)
        summary += "\t<li>Name: " + name + "</li>\n"

        # Add the activity date.
        if Keys.ACTIVITY_TIME_KEY in activity:
            summary += "\t<li>Start Time: " + App.timestamp_code_to_str(activity[Keys.ACTIVITY_TIME_KEY]) + "</li>\n"

        # Controls are only allowed if the user viewing the activity owns it.
        if belongs_to_current_user:
            details_controls_str = "<td><button type=\"button\" onclick=\"return refresh_analysis()\">Refresh Analysis</button></td><tr>\n"
        else:
            details_controls_str = ""

        # List the tags.
        tags_str = self.render_tags(activity, logged_in)

        # List the comments.
        comments_str = self.render_comments(activity, logged_in)

        # List the export options.
        exports_str = self.render_export_control(logged_in, False, Keys.APP_ACCELEROMETER_KEY in activity)

        # Render the delete control.
        delete_str = self.render_delete_control(logged_in)

        # Build the page title.
        if is_live:
            page_title = "Live Tracking"
        else:
            page_title = "Activity"

        my_template = Template(filename=self.lifting_activity_html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, email=email, name=user_realname, pagetitle=page_title, details=details, details_controls=details_controls_str, summary=summary, activityId=activity_id, xAxis=x_axis, yAxis=y_axis, zAxis=z_axis, tags=tags_str, comments=comments_str, exports=exports_str, delete=delete_str)

    def render_metadata_for_page(self, key, activity):
        """Helper function for processing meatadata and formatting it for display."""
        max_value = 0.0
        data_str = ""
        data = []
        if key in activity:
            data = activity[key]
        if data is not None and isinstance(data, list):
            for datum in data:
                time = datum.keys()[0]
                value = float(datum.values()[0])
                data_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"
                if value > max_value:
                    max_value = value
        return data_str, max_value

    def render_sensor_data_for_page(self, key, activity):
        """Helper function for processing sensor data and formatting it for display."""
        max_value = 0.0
        data_str = ""
        data = []
        if key in activity:
            data = activity[key]
        for datum in data:
            time = datum.keys()[0]
            value = float(datum.values()[0])
            data_str += "\t\t\t\t{ date: new Date(" + str(time) + "), value: " + str(value) + " },\n"
            if value > max_value:
                max_value = value
        return data_str, max_value

    def render_activity_name(self, activity):
        """Helper function for getting the activity name."""
        if Keys.ACTIVITY_NAME_KEY in activity:
            activity_name = activity[Keys.ACTIVITY_NAME_KEY]
        else:
            activity_name = Keys.UNNAMED_ACTIVITY_TITLE
        if len(activity_name) == 0:
            activity_name = Keys.UNNAMED_ACTIVITY_TITLE
        return activity_name

    def render_activity_type(self, activity):
        """Helper function for getting the activity type."""
        if Keys.ACTIVITY_TYPE_KEY in activity:
            activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
        else:
            activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY
        if len(activity_type) == 0:
            activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY
        return activity_type

    def render_array(self, array):
        """Helper function for converting an array (list) to a comma-separated string."""
        result = ""
        for item in array:
            if len(result) > 0:
                result += ","
            result += str(item)
        return result

    def render_page_for_mapped_activity(self, email, user_realname, activity_id, activity, activity_user_id, logged_in_userid, belongs_to_current_user, is_live):
        """Helper function for rendering the map corresonding to a specific activity."""

        # Is the user logged in?
        logged_in = logged_in_userid is not None

        locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
        if locations is None or len(locations) == 0:
            my_template = Template(filename=self.error_logged_in_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, error="There is no data for the specified activity.")

        route = ""
        center_lat = 0
        center_lon = 0
        last_lat = 0
        last_lon = 0

        for location in locations:
            route += "\t\t\t\tnewCoord(" + str(location[Keys.LOCATION_LAT_KEY]) + ", " + str(location[Keys.LOCATION_LON_KEY]) + "),\n"
            last_loc = location

        if len(locations) > 0:
            first_loc = locations[0]
            center_lat = first_loc[Keys.LOCATION_LAT_KEY]
            center_lon = first_loc[Keys.LOCATION_LON_KEY]
            last_lat = last_loc[Keys.LOCATION_LAT_KEY]
            last_lon = last_loc[Keys.LOCATION_LON_KEY]

        # Get all the things.
        current_speeds_str, _ = self.render_metadata_for_page(Keys.APP_CURRENT_SPEED_KEY, activity)
        heart_rates_str, max_heart_rate = self.render_sensor_data_for_page(Keys.APP_HEART_RATE_KEY, activity)
        cadences_str, max_cadence = self.render_sensor_data_for_page(Keys.APP_CADENCE_KEY, activity)
        powers_str, max_power = self.render_sensor_data_for_page(Keys.APP_POWER_KEY, activity)
        name = self.render_activity_name(activity)
        activity_type = self.render_activity_type(activity)

        # Compute location-based things.
        location_analyzer = LocationAnalyzer.LocationAnalyzer(activity_type)
        location_analyzer.append_locations(locations)

        # Compute the power zones.
        power_zones_str = ""
        ftp = self.data_mgr.retrieve_user_estimated_ftp(activity_user_id)
        if ftp is not None and Keys.APP_POWER_KEY in activity:
            power_zone_distribution = self.data_mgr.compute_power_zone_distribution(ftp[0], activity[Keys.APP_POWER_KEY])
            power_zones_str = "\t\t" + self.render_array(power_zone_distribution)

        # Retrieve cached summary data. If summary data has not been computed, then add this activity to the queue and move on without it.
        summary_data = self.data_mgr.retrieve_activity_summary(activity_id)
        if summary_data is None or len(summary_data) == 0:
            self.data_mgr.analyze(activity, activity_user_id)

        # Build the summary data view.
        summary = "<ul>\n"

        # Add the activity type.
        summary += "\t<li>Activity Type: " + activity_type + "</li>\n"

        # Add the activity date.
        if Keys.ACTIVITY_TIME_KEY in activity:
            summary += "\t<li>Start Time: " + App.timestamp_code_to_str(activity[Keys.ACTIVITY_TIME_KEY]) + "</li>\n"

        # Add the activity name.
        summary += "\t<li>Name: " + name + "</li>\n"

        if location_analyzer.total_distance is not None:
            value, value_units = Units.convert_to_preferred_distance_units(self.user_mgr, logged_in_userid, location_analyzer.total_distance, Units.UNITS_DISTANCE_METERS)
            summary += "\t<li>Distance: {:.2f} ".format(value) + Units.get_distance_units_str(value_units) + "</li>\n"
        if location_analyzer.avg_speed is not None:
            value, value_distance_units, value_time_units = Units.convert_to_preferred_speed_units(self.user_mgr, logged_in_userid, location_analyzer.avg_speed, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS)
            summary += "\t<li>Avg. Speed: {:.2f} ".format(value) + Units.get_speed_units_str(value_distance_units, value_time_units) + "</li>\n"

        # Add summary data that was computed out-of-band and cached.
        if summary_data is not None:

            if Keys.BEST_SPEED in summary_data:
                summary += "\t<li>Max. Speed: " + Units.convert_to_preferred_units_str(self.user_mgr, logged_in_userid, summary_data[Keys.BEST_SPEED], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, Keys.BEST_SPEED) + "</li>\n"
            if Keys.BEST_1K in summary_data:
                summary += "\t<li>Best KM: " + Units.convert_to_preferred_units_str(self.user_mgr, logged_in_userid, summary_data[Keys.BEST_1K], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, Keys.BEST_1K) + "</li>\n"
            if Keys.BEST_MILE in summary_data:
                summary += "\t<li>Best Mile: " + Units.convert_to_preferred_units_str(self.user_mgr, logged_in_userid, summary_data[Keys.BEST_MILE], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, Keys.BEST_MILE) + "</li>\n"

        if max_heart_rate > 1:
            summary += "\t<li>Max. Heart Rate: {:.2f} ".format(max_heart_rate) + Units.get_heart_rate_units_str() + "</li>\n"
        if max_cadence:
            summary += "\t<li>Max. Cadence: {:.1f} ".format(max_cadence) + Units.get_cadence_units_str() + "</li>\n"
        if max_power:
            summary += "\t<li>Max. Power: {:.2f} ".format(max_power) + Units.get_power_units_str() + "</li>\n"

        # Add power-related summary data that was computed out-of-band and cached.
        if summary_data is not None:
            if Keys.NORMALIZED_POWER in summary_data:
                normalized_power = summary_data[Keys.NORMALIZED_POWER]
                summary += "\t<li>Normalized Power: {:.2f} ".format(normalized_power) + Units.get_power_units_str() + "</li>\n"

        # Build the detailed analysis table.
        details_str = ""
        excluded_keys = [ Keys.LONGEST_DISTANCE ]
        if summary_data is not None:
            for key in sorted(summary_data):
                if key not in excluded_keys:
                    details_str += "<td><b>"
                    details_str += key
                    details_str += "</b></td><td>"
                    value = summary_data[key]
                    details_str += Units.convert_to_preferred_units_str(self.user_mgr, logged_in_userid, value, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, key)
                    details_str += "</td><tr>"
        if len(details_str) == 0:
            details_str = "<td><b>No data</b></td><tr>"

        # Controls are only allowed if the user viewing the activity owns it.
        if belongs_to_current_user:
            details_controls_str = "<td><button type=\"button\" onclick=\"return refresh_analysis()\">Refresh Analysis</button></td><tr>\n"
        else:
            details_controls_str = ""

        # List the tags.
        tags_str = self.render_tags(activity, logged_in)

        # List the gear.
        gear_str = self.render_gear(activity_user_id, activity_type, activity, logged_in)

        # List the comments.
        comments_str = self.render_comments(activity, logged_in)

        # List the export options.
        exports_str = self.render_export_control(logged_in, True, Keys.APP_ACCELEROMETER_KEY in activity)

        # Render the delete control.
        delete_str = self.render_delete_control(logged_in)

        # Build the page title.
        if is_live:
            page_title = "Live Tracking"
        else:
            page_title = "Activity"

        # If a google maps key was provided then use google maps, otherwise use open street map.
        if self.google_maps_key:
            my_template = Template(filename=self.map_single_google_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, email=email, name=user_realname, pagetitle=page_title, summary=summary, googleMapsKey=self.google_maps_key, centerLat=center_lat, lastLat=last_lat, lastLon=last_lon, centerLon=center_lon, route=route, routeLen=len(locations), activityId=activity_id, currentSpeeds=current_speeds_str, heartRates=heart_rates_str, cadences=cadences_str, powers=powers_str, powerZones=power_zones_str, details=details_str, details_controls=details_controls_str, tags=tags_str, gear=gear_str, comments=comments_str, exports=exports_str, delete=delete_str)
        else:
            my_template = Template(filename=self.map_single_osm_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, email=email, name=user_realname, pagetitle=page_title, summary=summary, centerLat=center_lat, lastLat=last_lat, lastLon=last_lon, centerLon=center_lon, route=route, routeLen=len(locations), activityId=activity_id, currentSpeeds=current_speeds_str, heartRates=heart_rates_str, cadences=cadences_str, powers=powers_str, powerZones=power_zones_str, details=details_str, details_controls=details_controls_str, tags=tags_str, gear=gear_str, comments=comments_str, exports=exports_str, delete=delete_str)

    def render_page_for_activity(self, activity, email, user_realname, activity_id, activity_user_id, logged_in_userid, belongs_to_current_user, is_live):
        """Helper function for rendering the page corresonding to a specific activity."""

        try:
            if Keys.ACTIVITY_LOCATIONS_KEY in activity and len(activity[Keys.ACTIVITY_LOCATIONS_KEY]) > 0:
                return self.render_page_for_mapped_activity(email, user_realname, activity_id, activity, activity_user_id, logged_in_userid, belongs_to_current_user, is_live)
            elif Keys.APP_ACCELEROMETER_KEY in activity or Keys.APP_SETS_KEY in activity:
                return self.render_page_for_lifting_activity(email, user_realname, activity_id, activity, activity_user_id, logged_in_userid, belongs_to_current_user, is_live)
            else:
                my_template = Template(filename=self.error_logged_in_html_file, module_directory=self.tempmod_dir)
                return my_template.render(nav=self.create_navbar(logged_in_userid is not None), product=PRODUCT_NAME, root_url=self.root_url, error="There is no data for the specified activity.")
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + App.activity.__name__)
        return self.error()

    def render_page_for_multiple_mapped_activities(self, email, user_realname, device_strs, user_id, logged_in):
        """Helper function for rendering the map to track multiple devices."""

        if device_strs is None:
            my_template = Template(filename=self.error_logged_in_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, error="No device IDs were specified.")

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

            locations = self.data_mgr.retrieve_locations(activity_id)
            if locations is None:
                continue

            route_coordinates += "\t\t\tvar routeCoordinates" + str(device_index) + " = \n\t\t\t[\n"
            for location in locations:
                route_coordinates += "\t\t\t\tnewCoord(" + str(location[Keys.LOCATION_LAT_KEY]) + ", " + str(location[Keys.LOCATION_LON_KEY]) + "),\n"
                last_loc = location
            route_coordinates += "\t\t\t];\n"
            route_coordinates += "\t\t\taddRoute(routeCoordinates" + str(device_index) + ");\n\n"

            if len(locations) > 0:
                first_loc = locations[0]
                center_lat = first_loc[Keys.LOCATION_LAT_KEY]
                center_lon = first_loc[Keys.LOCATION_LON_KEY]
                last_lat = last_loc[Keys.LOCATION_LAT_KEY]
                last_lon = last_loc[Keys.LOCATION_LON_KEY]

        my_template = Template(filename=self.map_multi_html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, email=email, name=user_realname, googleMapsKey=self.google_maps_key, centerLat=center_lat, centerLon=center_lon, lastLat=last_lat, lastLon=last_lon, routeCoordinates=route_coordinates, routeLen=len(locations), userId=str(user_id))

    @staticmethod
    def render_user_row(user):
        """Helper function for creating a table row describing a user."""
        row = "<tr>"
        row += "<td>"
        row += user[Keys.USERNAME_KEY]
        row += "</td>"
        row += "<td>"
        row += user[Keys.REALNAME_KEY]
        row += "</td>"
        row += "</tr>\n"
        return row

    def error(self, error_str=None):
        """Renders the error page."""
        try:
            error_html_file = os.path.join(self.root_dir, HTML_DIR, 'error.html')
            my_template = Template(filename=error_html_file, module_directory=self.tempmod_dir)
            if error_str is None:
                error_str = "Internal Error."
            return my_template.render(product=PRODUCT_NAME, root_url=self.root_url, error=error_str)
        except:
            pass
        return ""

    @statistics
    def live(self, device_str):
        """Renders the map page for the current activity from a single device."""

        # Get the logged in user (if any).
        logged_in_userid = None
        logged_in_username = self.user_mgr.get_logged_in_user()
        if logged_in_username is not None:
            logged_in_userid, _, _ = self.user_mgr.retrieve_user(logged_in_username)

        # Determine the ID of the most recent activity logged from the specified device.
        activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
        if activity_id is None:
            return self.error()

        # Determine who owns the device.
        device_user = self.user_mgr.retrieve_user_from_device(device_str)
        activity_user_id = device_user[Keys.DATABASE_ID_KEY]
        belongs_to_current_user = str(activity_user_id) == str(logged_in_userid)

        # Load the activity.
        activity = self.data_mgr.retrieve_activity(activity_id)

        # Is the activity still live? After one day, the activity is no longer considered live.
        end_time = self.data_mgr.compute_end_time(activity) / 1000
        now = time.time()
        diff = now - end_time
        diff_hours = diff / 60 / 60
        diff_days = diff_hours / 24
        if diff_days >= 1.0:
            return self.error("The user has not posted any data in over 24 hours.")

        # Determine if the current user can view the activity.
        if not (self.data_mgr.is_activity_public(activity) or belongs_to_current_user):
            return self.error("The requested activity is not public.")

        # Render from template.
        return self.render_page_for_activity(activity, device_user[Keys.USERNAME_KEY], device_user[Keys.REALNAME_KEY], activity_id, activity_user_id, logged_in_userid, belongs_to_current_user, True)

    @statistics
    def activity(self, activity_id):
        """Renders the map page for an activity."""

        # Get the logged in user (if any).
        logged_in_userid = None
        logged_in_username = self.user_mgr.get_logged_in_user()
        if logged_in_username is not None:
            logged_in_userid, _, _ = self.user_mgr.retrieve_user(logged_in_username)

        # Load the activity.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if activity is None:
            return self.error("The requested activity does not exist.")

        # Determine who owns the device, and hence the activity.
        activity_user_id, activity_username, activity_user_realname = self.user_mgr.get_activity_user(activity)
        belongs_to_current_user = str(activity_user_id) == str(logged_in_userid)
        if activity_username is None:
            activity_username = ""
        if activity_user_realname is None:
            activity_user_realname = ""

        # Determine if the current user can view the activity.
        if not (self.data_mgr.is_activity_public(activity) or belongs_to_current_user):
            return self.error("The requested activity is not public.")

        # Render from template.
        return self.render_page_for_activity(activity, activity_username, activity_user_realname, activity_id, activity_user_id, logged_in_userid, belongs_to_current_user, False)

    @statistics
    def device(self, device_str):
        """Renders the map page for a single device."""

        # Get the logged in user (if any).
        logged_in_userid = None
        logged_in_username = self.user_mgr.get_logged_in_user()
        if logged_in_username is not None:
            logged_in_userid, _, _ = self.user_mgr.retrieve_user(logged_in_username)

        # Get the activity ID being requested. If one is not provided then get the latest activity for the device
        activity_id = cherrypy.request.params.get("activity_id")
        if activity_id is None:
            activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
            if activity_id is None:
                return self.error()

        # Determine who owns the device.
        device_user = self.user_mgr.retrieve_user_from_device(device_str)
        activity_user_id = device_user[Keys.DATABASE_ID_KEY]
        belongs_to_current_user = str(activity_user_id) == str(logged_in_userid)

        # Load the activity.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if activity is None:
            return self.error("The requested activity does not exist.")

        # Determine if the current user can view the activity.
        if not (self.data_mgr.is_activity_public(activity) or belongs_to_current_user):
            return self.error("The requested activity is not public.")

        # Render from template.
        return self.render_page_for_activity(activity, device_user[Keys.USERNAME_KEY], device_user[Keys.REALNAME_KEY], activity_id, activity_user_id, logged_in_userid, belongs_to_current_user, False)

    @statistics
    def my_activities(self):
        """Renders the list of the specified user's activities."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'my_activities.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname)

    @statistics
    def all_activities(self):
        """Renders the list of all activities the specified user is allowed to view."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'all_activities.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname)

    def render_personal_records(self, user_id, cycling_bests, running_bests):
        """Helper function that renders the table rows used to show personal bests."""
        bests_str = ""
        if cycling_bests is not None and len(cycling_bests) > 0:
            bests_str += "<h3>Cycling Efforts</h3>\n"
            bests_str += "<table>\n"
            for record_name in cycling_bests:
                record = cycling_bests[record_name]
                record_value = record[0]
                activity_id = record[1]
                record_str = Units.convert_to_preferred_units_str(self.user_mgr, user_id, record_value, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, record_name)

                bests_str += "<td>"
                bests_str += record_name
                bests_str += "</td><td><a href=\"" + self.root_url + "/activity/" + activity_id + "\">" + record_str + "</a></td><tr>\n"
            bests_str += "</table>\n"
        if running_bests is not None and len(running_bests) > 0:
            bests_str += "<h3>Running Efforts</h3>\n"
            bests_str += "<table>\n"
            for record_name in running_bests:
                record = running_bests[record_name]
                record_value = record[0]
                activity_id = record[1]
                record_str = Units.convert_to_preferred_units_str(self.user_mgr, user_id, record_value, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, record_name)

                bests_str += "<td>"
                bests_str += record_name
                bests_str += "</td><td><a href=\"" + self.root_url + "/activity/" + activity_id + "\">" + record_str + "</a></td><tr>\n"
            bests_str += "</table>\n"
        return bests_str

    @statistics
    def workouts(self):
        """Renders the list of all workouts the specified user is allowed to view."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Show the relevant PRs.
        cycling_bests, running_bests = self.data_mgr.compute_recent_bests(user_id, DataMgr.SIX_MONTHS)
        bests_str = self.render_personal_records(user_id, cycling_bests, running_bests)

        # Show the running training paces.
        run_paces = self.data_mgr.compute_run_training_paces(user_id, running_bests)
        if run_paces:
            run_paces_str = "<table>"
            for run_pace in run_paces:
                run_paces_str += "<td>"
                run_paces_str += run_pace
                run_paces_str += "</td><td>"
                run_paces_str += Units.convert_to_preferred_units_str(self.user_mgr, user_id, run_paces[run_pace], Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_MINUTES, run_pace)
                run_paces_str += "</td><tr>"
            run_paces_str += "</table>"
        else:
            run_paces_str = "Not calculated."

        # Set the default goals based on previous selections.
        goal = self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_KEY)
        goal_date = self.user_mgr.retrieve_user_setting(user_id, Keys.GOAL_DATE_KEY)
        goals_str = ""
        for possible_goal in Keys.GOALS:
            goals_str += "\t\t\t<option value=\"" + possible_goal + "\""
            if possible_goal.lower() == goal.lower():
                goals_str += " selected"
            goals_str += ">" + possible_goal + "</option>\n"

        # Show plans that have already been generated.
        plans_str = ""
        workouts = self.data_mgr.retrieve_workouts_for_user(user_id)
        if workouts is not None:
            plans_str = "<table>"
            for workout in workouts:
                plans_str += "<td>"
                plans_str += "</td><tr>"
            plans_str += "</table>"

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'workouts.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, bests=bests_str, runpaces=run_paces_str, plans=plans_str, goals=goals_str, goal_date=goal_date)

    @statistics
    def gear(self):
        """Renders the list of all gear belonging to the logged in user."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        num_bikes = 0
        num_shoes = 0
        bikes = "<table>"
        shoes = "<table>"
        gear_list = self.data_mgr.retrieve_gear_for_user(user_id)
        for gear in gear_list:
            if Keys.GEAR_TYPE_KEY in gear:
                row_str = ""
                if Keys.GEAR_NAME_KEY in gear:
                    row_str += "<td>"
                    row_str += gear[Keys.GEAR_NAME_KEY]
                    row_str += "</td><td>"
                    row_str += gear[Keys.GEAR_DESCRIPTION_KEY]
                    row_str += "</td><td>"
                    row_str += "<script>document.write(new Date(" + str(gear[Keys.GEAR_ADD_TIME_KEY]) + " * 1000))</script>"
                    row_str += "</td>"
                row_str += "<tr>"
                gear_type = gear[Keys.GEAR_TYPE_KEY]
                if gear_type == Keys.GEAR_TYPE_BIKE:
                    if num_bikes == 0:
                        bikes += "<td><b>Name</b></td><td><b>Description</b></td><td><b>Date Added</b></td><tr>"
                    bikes += row_str
                    num_bikes = num_bikes + 1
                elif gear_type == Keys.GEAR_TYPE_SHOES:
                    if num_shoes == 0:
                        shoes += "<td><b>Name</b></td><td><b>Description</b></td><td><b>Date Added</b></td><tr>"
                    shoes += row_str
                    num_shoes = num_shoes + 1
        bikes += "</table>"
        shoes += "</table>"
        if num_bikes == 0:
            bikes = "<b>None</b>"
        if num_shoes == 0:
            shoes = "<b>None</b>"

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'gear.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, bikes=bikes, shoes=shoes)

    @statistics
    def following(self):
        """Renders the list of users the specified user is following."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Get the list of users followed by the logged in user.
        users_following = self.user_mgr.list_users_followed(user_id)
        users_list_str = "Not currently following anyone."
        if users_following is not None and isinstance(users_following, list):
            if len(users_following) > 0:
                users_list_str = ""
                for user in users_following:
                    users_list_str += self.render_user_row(user)

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'following.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, users_list=users_list_str)

    @statistics
    def followers(self):
        """Renders the list of users that are following the specified user."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Get the list of users following the logged in user.
        users_followed_by = self.user_mgr.list_followers(user_id)
        users_list_str = "Not currently being followed by anyone."
        if users_followed_by is not None and isinstance(users_followed_by, list):
            if len(users_followed_by) > 0:
                users_list_str = ""
                for user in users_followed_by:
                    users_list_str += self.render_user_row(user)

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'followers.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, users_list=users_list_str)

    @statistics
    def device_list(self):
        """Renders the list of a user's devices."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Get the list of devices that are associated with the user.
        devices = self.user_mgr.retrieve_user_devices(user_id)

        # Build a list of table rows from the device information.
        device_list_str = ""
        if devices is not None and isinstance(devices, list):
            device_list_str += "<td><b>Unique Identifier</b></td><td><b>Last Heard From</b></td><tr>\n"
            for device in devices:
                activity = self.data_mgr.retrieve_most_recent_activity_for_device(device)
                device_list_str += "\t\t<tr>"
                device_list_str += "<td><a href=\"" + self.root_url + "/device/" + device + "\">"
                device_list_str += device
                device_list_str += "</a></td><td>"
                if activity is not None:
                    device_list_str += "<script>document.write(unix_time_to_local_string(" + str(activity[Keys.ACTIVITY_TIME_KEY]) + "))</script>"
                device_list_str += "</td></tr>\n"

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'device_list.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, device_list=device_list_str)

    @statistics
    def upload(self, ufile):
        """Processes an request from the upload form."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, _ = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Parse the file and store it's contents in the database.
        file_data = ufile.file.read()
        self.data_mgr.import_file(username, user_id, file_data, ufile.filename)

        raise RedirectException(DEFAULT_LOGGED_IN_URL)

    @statistics
    def manual_entry(self, activity_type):
        """Called when the user selects an activity type, indicatig they want to make a manual data entry."""
        print(activity_type)

    @statistics
    def import_activity(self):
        """Renders the import page."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Build the list options for manual entry.
        activity_type_list = self.data_mgr.retrieve_activity_types()
        activity_type_list_str = "\t\t\t<option value=\"-\">-</option>\n"
        for activity_type in activity_type_list:
            activity_type_list_str += "\t\t\t<option value=\"" + activity_type + "\">" + activity_type + "</option>\n"

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'import.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, activity_type_list=activity_type_list_str)

    @statistics
    def summary(self):
        """Renders the user's summary page."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Render from the template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'summary.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname)

    @statistics
    def profile(self):
        """Renders the user's profile page."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Get the current settings.
        selected_birthday = self.user_mgr.retrieve_user_setting(user_id, Keys.BIRTHDAY_KEY)
        selected_height_metric = self.user_mgr.retrieve_user_setting(user_id, Keys.HEIGHT_KEY)
        selected_weight_metric = self.user_mgr.retrieve_user_setting(user_id, Keys.WEIGHT_KEY)
        selected_gender = self.user_mgr.retrieve_user_setting(user_id, Keys.GENDER_KEY)
        selected_resting_hr = self.user_mgr.retrieve_user_setting(user_id, Keys.RESTING_HEART_RATE_KEY)
        estimated_max_hr = self.user_mgr.retrieve_user_setting(user_id, Keys.ESTIMATED_MAX_HEART_RATE_KEY)

        # Render the user's height.
        if isinstance(selected_height_metric, float):
            selected_height_pref, height_units = Units.convert_to_preferred_height_units(self.user_mgr, user_id, selected_height_metric, Units.UNITS_DISTANCE_METERS)
            selected_height_str = "{:.1f}".format(selected_height_pref)
            height_units_str = Units.get_distance_units_str(height_units)
        else:
            selected_height_metric = None
            selected_height_str = ""
            height_units_str = Units.get_preferred_height_units_str(self.user_mgr, user_id)

        # Render the user's weight.
        if isinstance(selected_weight_metric, float):
            selected_weight_pref, weight_units = Units.convert_to_preferred_mass_units(self.user_mgr, user_id, selected_weight_metric, Units.UNITS_MASS_KG)
            selected_weight_str = "{:.1f}".format(selected_weight_pref)
            weight_units_str = Units.get_mass_units_str(weight_units)
        else:
            selected_weight_metric = None
            selected_weight_str = ""
            weight_units_str = Units.get_preferred_mass_units_str(self.user_mgr, user_id)

        # Render the gender option.
        gender_options = "\t\t<option value=\"Male\""
        if selected_gender == Keys.GENDER_MALE_KEY:
            gender_options += " selected"
        gender_options += ">Male</option>\n"
        gender_options += "\t\t<option value=\"Female\""
        if selected_gender == Keys.GENDER_FEMALE_KEY:
            gender_options += " selected"
        gender_options += ">Female</option>"

        # Render the user's resting heart rate.
        if isinstance(selected_resting_hr, float):
            resting_hr_str = "{:.1f}".format(selected_resting_hr)
        else:
            resting_hr_str = ""
            selected_resting_hr = None

        # Get the user's BMI.
        if selected_height_metric and selected_weight_metric:
            calc = BmiCalculator.BmiCalculator()
            bmi = calc.estimate_bmi(selected_weight_metric, selected_height_metric)
            bmi_str = "{:.1f}".format(bmi)
        else:
            bmi_str = "Not calculated."
    
        # Get the user's VO2Max.
        if selected_resting_hr and isinstance(estimated_max_hr, float):
            calc = VO2MaxCalculator.VO2MaxCalculator()
            vo2max_str = calc.estimate_vo2max_from_heart_rate(estimated_max_hr, selected_resting_hr)
            vo2max = "{:.1f}".format(vo2max_str)
        else:
            vo2max = "Not calculated."

        # Get the user's FTP.
        ftp = self.data_mgr.retrieve_user_estimated_ftp(user_id)
        if ftp is None:
            ftp_str = "Cycling activities with power data that was recorded in the last six months must be uploaded before your FTP can be estimated."
        else:
            ftp_str = "{:.1f} watts".format(ftp[0])

        # Get the user's heart rate zones.
        hr_zones = "No heart rate data exists."
        if isinstance(estimated_max_hr, float):
            zones = self.data_mgr.retrieve_heart_rate_zones(estimated_max_hr)
            if len(zones) > 0:
                hr_zones = "<table>\n"
                zone_index = 0
                for zone in zones:
                    hr_zones += "<td>Zone " + str(zone_index + 1) + "</td><td>"
                    if zone_index == 0:
                        hr_zones += "0 bpm to {:.1f} bpm</td><tr>\n".format(zone)
                    else:
                        hr_zones += "{:.1f} bpm to {:.1f} bpm</td><tr>\n".format(zones[zone_index - 1], zone)
                    hr_zones += "</td><tr>\n"
                    zone_index = zone_index + 1
                hr_zones += "</table>\n"

        # Get the user's cycling power training zones.
        power_zones = "Cycling power zones cannot be calculated until the user's FTP (functional threshold power) is set."
        if isinstance(ftp, float):
            zones = self.data_mgr.retrieve_power_training_zones(ftp)
            if len(zones) > 0:
                power_zones = "<table>\n"
                zone_index = 0
                for zone in zones:
                    power_zones += "<td>Zone " + str(zone_index + 1) + "</td><td>"
                    if zone_index == 0:
                        power_zones += "0 watts to {:.1f} watts</td><tr>".format(zone)
                    else:
                        power_zones += "{:.1f} watts to {:.1f} watts</td><tr>\n".format(zones[zone_index - 1], zone)
                    zone_index = zone_index + 1
                power_zones += "</table>\n"

        # Get the user's personal recorsd.
        prs = ""
        record_groups = self.data_mgr.retrieve_user_personal_records(user_id)
        for record_group in record_groups:
            record_dict = record_groups[record_group]
            if len(record_dict) > 0:
                prs += "<h3>" + record_group + "</h3>\n"
                prs += "<table>\n"
                for record_name in record_dict:
                    record = record_dict[record_name]
                    record_value = record[0]
                    activity_id = record[1]
                    record_str = Units.convert_to_preferred_units_str(self.user_mgr, user_id, record_value, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, record_name)

                    prs += "<td>"
                    prs += record_name
                    prs += "</td><td><a href=\"" + self.root_url + "/activity/" + activity_id + "\">" + record_str + "</a></td><tr>\n"
                prs += "</table>\n"

        # Render from the template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'profile.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, birthday=selected_birthday, weight=selected_weight_str, weight_units=weight_units_str, height=selected_height_str, height_units=height_units_str, gender_options=gender_options, resting_hr=resting_hr_str, bmi=bmi_str, vo2max=vo2max, ftp=ftp_str, hr_zones=hr_zones, power_zones=power_zones, prs=prs)

    @statistics
    def settings(self):
        """Renders the user's settings page."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Get the current settings.
        selected_default_privacy = self.user_mgr.retrieve_user_setting(user_id, Keys.DEFAULT_PRIVACY)
        selected_units = self.user_mgr.retrieve_user_setting(user_id, Keys.PREFERRED_UNITS_KEY)

        # Render the privacy option.
        privacy_options = "\t\t<option value=\"Public\""
        if selected_default_privacy == Keys.ACTIVITY_VISIBILITY_PUBLIC:
            privacy_options += " selected"
        privacy_options += ">Public</option>\n"
        privacy_options += "\t\t<option value=\"Private\""
        if selected_default_privacy == Keys.ACTIVITY_VISIBILITY_PRIVATE:
            privacy_options += " selected"
        privacy_options += ">Private</option>"

        # Render the units
        unit_options = "\t\t<option value=\"Metric\""
        if selected_units == Keys.UNITS_METRIC_KEY:
            unit_options += " selected"
        unit_options += ">Metric</option>\n"
        unit_options += "\t\t<option value=\"Standard\""
        if selected_units == Keys.UNITS_STANDARD_KEY:
            unit_options += " selected"
        unit_options += ">Standard</option>"

        # Render from the template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'settings.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, privacy_options=privacy_options, unit_options=unit_options)

    @statistics
    def api(self, user_id, method, params):
        """Handles an API request."""
        api = Api.Api(self.user_mgr, self.data_mgr, self.tempfile_dir, user_id, self.root_url)
        handled, response = api.handle_api_1_0_request(method, params)
        return handled, response

    @statistics
    def login(self):
        """Renders the login page."""

        # If a user is already logged in then go straight to the landing page.
        username = self.user_mgr.get_logged_in_user()
        if username is not None:
            raise RedirectException(DEFAULT_LOGGED_IN_URL)

        html = ""
        readme_file_name = os.path.join(self.root_dir, 'README.md')
        with open(readme_file_name, 'r') as readme_file:
            md = readme_file.read()
            extensions = ['extra', 'smarty']
            html = markdown.markdown(md, extensions=extensions, output_format='html5')

        login_html_file = os.path.join(self.root_dir, HTML_DIR, 'login.html')
        my_template = Template(filename=login_html_file, module_directory=self.tempmod_dir)
        return my_template.render(product=PRODUCT_NAME, root_url=self.root_url, readme=html)

    @statistics
    def create_login(self):
        """Renders the create login page."""
        create_login_html_file = os.path.join(self.root_dir, HTML_DIR, 'create_login.html')
        my_template = Template(filename=create_login_html_file, module_directory=self.tempmod_dir)
        return my_template.render(product=PRODUCT_NAME, root_url=self.root_url)

    @statistics
    def logout(self):
        """Ends the logged in session."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Clear the session.
        self.user_mgr.clear_session()

        # Send the user back to the login screen.
        raise RedirectException(LOGIN_URL)

    @statistics
    def about(self):
        """Renders the about page."""
        about_html_file = os.path.join(self.root_dir, HTML_DIR, 'about.html')
        my_template = Template(filename=about_html_file, module_directory=self.tempmod_dir)
        return my_template.render(product=PRODUCT_NAME, root_url=self.root_url)

    @statistics
    def status(self):
        """Renders the status page. Used as a simple way to tell if the site is up."""
        return "Up"
