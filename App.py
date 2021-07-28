# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2017-2020 Mike Simms
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Main application, contains all web page handlers"""

import datetime
import inspect
import json
import logging
import markdown
import os
import sys
import threading
import time
import timeit
import traceback
import cProfile
import pstats

try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3

import Keys
import Api
import IcalServer
import InputChecker
import Perf
import Units

from dateutil.tz import tzlocal
from mako.template import Template

# Locate and load the Distance calculations module.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
distancedir = os.path.join(currentdir, 'LibMath', 'python', 'distance')
sys.path.insert(0, distancedir)
import distance


PRODUCT_NAME = 'OpenWorkout'

LOGIN_URL = '/login'
DEFAULT_LOGGED_IN_URL = '/all_activities'
TASK_STATUS_URL = '/task_status'
HTML_DIR = 'html'
MEDIA_DIR = 'media'
ZWIFT_WATOPIA_MAP_FILE_NAME = 'watopia.png'
ZWIFT_CRIT_CITY_MAP_FILE_NAME = 'crit_city.png'
ZWIFT_MAKURI_ISLANDS_MAP_FILE_NAME = 'makuri_islands.png'

class RedirectException(Exception):
    """This is thrown when the app needs to redirect to another page."""

    def __init__(self, url):
        self.url = url
        super(RedirectException, self).__init__()


class App(object):
    """Class containing the URL handlers."""

    def __init__(self, user_mgr, data_mgr, root_dir, root_url, google_maps_key, enable_profiling, debug):
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.root_dir = root_dir
        self.root_url = root_url
        self.tempfile_dir = os.path.join(self.root_dir, 'tempfile')

        # We'll use different tempmod dirs for python2 and python3 so we can switch between them without frustration.
        if sys.version_info[0] < 3:
            self.tempmod_dir = os.path.join(self.root_dir, 'tempmod2')
        else:
            self.tempmod_dir = os.path.join(self.root_dir, 'tempmod3')

        self.google_maps_key = google_maps_key
        self.debug = debug
        self.zwift_watopia_map_file = os.path.join(root_dir, MEDIA_DIR, ZWIFT_WATOPIA_MAP_FILE_NAME)
        self.zwift_crit_city_map_file = os.path.join(root_dir, MEDIA_DIR, ZWIFT_CRIT_CITY_MAP_FILE_NAME)
        self.zwift_makuri_islands_map_file = os.path.join(root_dir, MEDIA_DIR, ZWIFT_MAKURI_ISLANDS_MAP_FILE_NAME)
        self.zwift_html_file = os.path.join(root_dir, HTML_DIR, 'zwift.html')
        self.unmapped_activity_html_file = os.path.join(root_dir, HTML_DIR, 'unmapped_activity.html')
        self.map_single_osm_html_file = os.path.join(root_dir, HTML_DIR, 'map_single_osm.html')
        self.map_single_google_html_file = os.path.join(root_dir, HTML_DIR, 'map_single_google.html')
        self.map_multi_html_file = os.path.join(root_dir, HTML_DIR, 'map_multi_google.html')
        self.error_logged_in_html_file = os.path.join(root_dir, HTML_DIR, 'error_logged_in.html')
        self.error_activity_html_file = os.path.join(root_dir, HTML_DIR, 'error_activity.html')
        self.ical_server = IcalServer.IcalServer(user_mgr, data_mgr, self.root_url)

        self.logged_in_navbar = "<nav>\n\t<ul>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/my_activities/\">My Activities</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/all_activities/\">All Activities</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/workouts/\">Workouts</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/pace_plans/\">Pace Plans</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/statistics/\">Statistics</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/gear/\">Gear</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/device_list/\">Devices</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/friends/\">Friends</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/import_activity/\">Import</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/profile/\">Profile</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/settings/\">Settings</a></li>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/logout/\">Log Out</a></li>\n" \
            "\t</ul>\n"
        self.logged_out_navbar = "<nav>\n\t<ul>\n" \
            "\t\t<li><a href=\"" + self.root_url + "/login/\">Log In</a></li>\n" \
            "\t</ul>\n"

        self.tempfile_dir = os.path.join(root_dir, 'tempfile')
        if not os.path.exists(self.tempfile_dir):
            os.makedirs(self.tempfile_dir)

        if enable_profiling:
            print("Start profiling...")
            self.pr = cProfile.Profile()
            self.pr.enable()
        else:
            self.pr = None

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
        if self.pr is not None:
            print("Stop profiling...")
            self.pr.disable()
            s = StringIO.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(self.pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            print(s.getvalue())

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

    def create_navbar(self, logged_in):
        """Helper function for building the navigation bar."""
        if logged_in:
            return self.logged_in_navbar
        return self.logged_out_navbar

    def performance_stats(self):
        """Renders the application's performance statistics."""

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Make a copy of the data so we don't have to hold the lock.
        Perf.g_stats_lock.acquire()
        temp_stats_count = Perf.g_stats_count
        temp_stats_time = Perf.g_stats_time
        Perf.g_stats_lock.release()

        # Build a list of table rows from the device information.
        page_stats_str = "<td><b>Page</b></td><td><b>Num Accesses</b></td><td><b>Avg Time (secs)</b></td><tr>\n"
        for key, count_value in temp_stats_count.iteritems():
            page_stats_str += "\t\t<tr><td>"
            page_stats_str += str(key)
            page_stats_str += "</td><td>"
            page_stats_str += str(count_value)
            page_stats_str += "</td><td>"
            if key in temp_stats_time and count_value > 0:
                total_time = temp_stats_time[key]
                avg_time = total_time / count_value
                page_stats_str += str(avg_time)
            page_stats_str += "</td></tr>\n"

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

    def render_simple_page(self, template_file_name, **kwargs):
        """Renders a basic page from the specified template. This exists because a lot of pages only need this to be rendered."""

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
        html_file = os.path.join(self.root_dir, HTML_DIR, template_file_name)
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, **kwargs)

    def render_tags(self, activity, activity_user_id, belongs_to_current_user):
        """Helper function for building the tags string."""
        activity_tags = []
        if Keys.ACTIVITY_TAGS_KEY in activity:
            activity_tags = activity[Keys.ACTIVITY_TAGS_KEY]

        if activity_user_id is not None and Keys.ACTIVITY_TYPE_KEY in activity:
            default_tags = self.data_mgr.list_available_tags_for_activity_type_and_user(activity_user_id, activity[Keys.ACTIVITY_TYPE_KEY])
        else:
            default_tags = self.data_mgr.list_default_tags()

        all_tags = []
        all_tags.extend(activity_tags)
        all_tags.extend(default_tags)
        all_tags = list(set(all_tags))
        all_tags.sort()

        tags_str = ""
        if all_tags is not None:
            for tag in all_tags:
                if tag in activity_tags:
                    tags_str += "<option selected=true"
                else:
                    tags_str += "<option"
                if not belongs_to_current_user:
                    tags_str += " disabled"
                tags_str += ">"
                tags_str += tag
                tags_str += "</option>\n"
        return tags_str

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
            comments_str += "<td><textarea rows=\"4\" class=\"comment\" style=\"width:50%;\" maxlength=\"512\" id=\"comment\"></textarea></td><tr>\n"
            comments_str += "<td><button type=\"button\" onclick=\"return create_comment()\">Post</button></td><tr>\n"
        elif len(comments_str) == 0:
            comments_str = "None"
        return comments_str

    @staticmethod
    def render_export_control(has_location_data, has_accel_data):
        """Helper function for building the exports string that appears on the activity details screens."""
        exports_str = "<td><select id=\"format\" >\n"
        if has_location_data:
            exports_str += "\t<option value=\"tcx\" selected>TCX</option>\n"
            exports_str += "\t<option value=\"gpx\">GPX</option>\n"
        if has_location_data or has_accel_data:
            exports_str += "\t<option value=\"csv\">CSV</option>\n"
        exports_str += "</select>\n</td><tr>\n"
        exports_str += "<td><button type=\"button\" onclick=\"return export_activity()\">Export</button></td><tr>\n"
        return exports_str

    @staticmethod
    def render_edit_controls():
        """Helper function for building the edit string that appears on the activity details screens."""
        edit_str  = "<td><button type=\"button\" onclick=\"return edit_activity()\" style=\"color:black\">Edit</button></td><tr>\n"
        edit_str += "<td><button type=\"button\" onclick=\"return add_photos()\" style=\"color:black\">Add Photos</button></td><tr>\n"
        return edit_str

    @staticmethod
    def render_delete_control():
        """Helper function for building the delete string that appears on the activity details screens."""
        delete_str = "<td><button type=\"button\" onclick=\"return delete_activity()\" style=\"color:red\">Delete</button></td><tr>\n"
        return delete_str

    @staticmethod
    def get_time_value_from_list_item(item, py_version):
        """Utility function because this logic appears in too many places."""
        if py_version < 3:
            time = int(float(item.keys()[0]))
            value = float(item.values()[0])
        else:
            time = int(float(list(item.keys())[0]))
            value = float(list(item.values())[0])
        return time, value

    def render_page_for_unmapped_activity(self, user_realname, activity_id, activity, activity_user_id, logged_in_username, belongs_to_current_user, is_live):
        """Helper function for rendering the page corresonding to a specific un-mapped activity."""

        # Is the user logged in?
        logged_in = logged_in_username is not None

        # Retrieve cached summary data. If summary data has not been computed, then add this activity to the queue and move on without it.
        summary_data = self.data_mgr.retrieve_activity_summary(activity_id)
        if summary_data is None or len(summary_data) == 0:
            self.data_mgr.analyze_activity(activity, activity_user_id)

        # Find the sets data.
        sets = None
        if Keys.APP_SETS_KEY in activity:
            sets = activity[Keys.APP_SETS_KEY]
        elif summary_data is not None and Keys.APP_SETS_KEY in summary_data:
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
        activity_type = App.render_activity_type(activity)
        summary += "\t<li>Activity Type: " + activity_type + "</li>\n"

        # Add the activity date.
        name = App.render_activity_name(activity)
        summary += "\t<li>Name: " + name + "</li>\n"

        # Add the activity date.
        if Keys.ACTIVITY_START_TIME_KEY in activity:
            summary += "\t<li>Start Time: <script>document.write(unix_time_to_local_string(" + str(activity[Keys.ACTIVITY_START_TIME_KEY]) + "))</script></li>\n"

        # Close the summary list.
        summary += "</ul>\n"

        # Controls are only allowed if the user viewing the activity owns it.
        if belongs_to_current_user:
            details_controls_str = "<td><button type=\"button\" onclick=\"return refresh_analysis()\">Refresh Analysis</button></td><tr>\n"
        else:
            details_controls_str = ""

        # Get the description.
        description_str = self.render_description_for_page(activity)

        # List the tags.
        tags_str = self.render_tags(activity, activity_user_id, belongs_to_current_user)

        # List the comments.
        comments_str = self.render_comments(activity, logged_in)

        # List the export options.
        exports_title_str = ""
        exports_str = ""
        if logged_in:
            exports_title_str = "<h3>Export</h3>"
            exports_str = App.render_export_control(False, Keys.APP_ACCELEROMETER_KEY in activity)

        # List the edit controls.
        edit_title_str = ""
        edit_str = ""
        if belongs_to_current_user:
            edit_title_str = "<h3>Edit</h3>"
            edit_str = App.render_edit_controls()

        # Render the delete control.
        delete_str = ""
        if belongs_to_current_user:
            delete_str = App.render_delete_control()

        # Build the page title.
        if is_live:
            page_title = "Live Tracking"
        else:
            page_title = "Activity"

        my_template = Template(filename=self.unmapped_activity_html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, pagetitle=page_title, description=description_str, details=details, details_controls=details_controls_str, summary=summary, activityId=activity_id, tags=tags_str, comments=comments_str, exports_title=exports_title_str, exports=exports_str, edit_title=edit_title_str, edit=edit_str, delete=delete_str)

    def render_description_for_page(self, activity):
        """Helper function for processing the activity description and formatting it for display."""
        description = ""
        if Keys.ACTIVITY_DESCRIPTION_KEY in activity:
            description = activity[Keys.ACTIVITY_DESCRIPTION_KEY]
        if len(description) == 0:
            description = "None"
        return description

    @staticmethod
    def render_intervals_str(intervals):
        """Helper function for building a description from the raw intervals description."""
        if intervals is None:
            return "None"
        num_intervals = len(intervals)
        if num_intervals <= 0:
            return "None"

        avg_interval_duration = 0.0
        avg_interval_length = 0.0
        avg_interval_speed = 0.0
        for interval in intervals:
            avg_interval_duration = avg_interval_duration + interval[2]
            avg_interval_length = avg_interval_length + interval[3]
            avg_interval_speed = avg_interval_speed + interval[4]
        avg_interval_duration = (avg_interval_duration / num_intervals) / 1000.0
        avg_interval_length = avg_interval_length / num_intervals
        avg_interval_speed = avg_interval_speed / num_intervals

        intervals_str = str(num_intervals) + " intervals averaging {:.2f}".format(avg_interval_length) + " meters at {:.2f}".format(avg_interval_duration) + " seconds/each."
        return intervals_str

    @staticmethod
    def render_activity_name(activity):
        """Helper function for getting the activity name."""
        if Keys.ACTIVITY_NAME_KEY in activity:
            activity_name = activity[Keys.ACTIVITY_NAME_KEY]
        else:
            activity_name = Keys.UNNAMED_ACTIVITY_TITLE
        if len(activity_name) == 0:
            activity_name = Keys.UNNAMED_ACTIVITY_TITLE
        return activity_name

    @staticmethod
    def render_activity_type(activity):
        """Helper function for getting the activity type."""
        if Keys.ACTIVITY_TYPE_KEY in activity:
            activity_type = activity[Keys.ACTIVITY_TYPE_KEY]
        else:
            activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY
        if len(activity_type) == 0:
            activity_type = Keys.TYPE_UNSPECIFIED_ACTIVITY_KEY
        return activity_type

    @staticmethod
    def render_difference_array(array):
        """Helper function for converting an array (list) to a comma-separated string."""
        result = ""
        last = 0
        for item in array:
            if len(result) > 0:
                result += ", "
            result += str(item - last)
            last = item
        return result

    @staticmethod
    def render_array_reversed(array):
        """Helper function for converting an array (list) to a comma-separated string."""
        result = ""
        for item in reversed(array):
            if len(result) > 0:
                result += ", "
            result += str(item)
        return result

    @staticmethod
    def is_activity_in_zwift_watopia(activity_type, lat, lon):
        """Zwift's Watopia is mapped over the Solomon Islands."""
        if activity_type == Keys.TYPE_VIRTUAL_CYCLING_KEY or activity_type == Keys.TYPE_VIRTUAL_RUNNING_KEY:
            distance_to_watopia_meters = distance.haversine_distance_ignore_altitude(lat, lon, -11.6364607214928, 166.972435712814)
            return (distance_to_watopia_meters < 25000)
        return False

    @staticmethod
    def is_activity_in_zwift_crit_city(activity_type, lat, lon):
        """Zwift's Crit City is mapped over the Solomon Islands."""
        if activity_type == Keys.TYPE_VIRTUAL_CYCLING_KEY or activity_type == Keys.TYPE_VIRTUAL_RUNNING_KEY:
            distance_to_watopia_meters = distance.haversine_distance_ignore_altitude(lat, lon, -10.383856371045113, 165.80203771591187)
            return (distance_to_watopia_meters < 10000)
        return False

    @staticmethod
    def is_activity_in_zwift_makuri_islands(activity_type, lat, lon):
        """Zwift's Makuri Islands is mapped over the Santa Cruz Islands in the Solomon Islands chain."""
        if activity_type == Keys.TYPE_VIRTUAL_CYCLING_KEY or activity_type == Keys.TYPE_VIRTUAL_RUNNING_KEY:
            distance_to_watopia_meters = distance.haversine_distance_ignore_altitude(lat, lon, -10.74387788772583, 165.8565080165863)
            return (distance_to_watopia_meters < 25000)
        return False

    def render_page_for_errored_activity(self, activity_id, logged_in, belongs_to_current_user):
        """Helper function for rendering an error page when attempting to view an activity with bad data."""
        delete_str = ""
        if belongs_to_current_user is not None:
            delete_str = App.render_delete_control()

        my_template = Template(filename=self.error_activity_html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, error="There is no data for the specified activity.", activityId=activity_id, delete=delete_str)

    def render_page_for_mapped_activity(self, user_realname, activity_id, activity, activity_user_id, logged_in_user_id, belongs_to_current_user, is_live):
        """Helper function for rendering the map corresonding to a specific activity."""

        # Is the user logged in?
        logged_in = logged_in_user_id is not None

        # Sanity check.
        locations = activity[Keys.ACTIVITY_LOCATIONS_KEY]
        if locations is None or len(locations) == 0:
            return self.render_page_for_errored_activity(activity_id, logged_in, belongs_to_current_user)

        last_loc = locations[-1]
        first_loc = locations[0]
        last_lat = last_loc[Keys.LOCATION_LAT_KEY]
        last_lon = last_loc[Keys.LOCATION_LON_KEY]
        duration = last_loc[Keys.LOCATION_TIME_KEY] - first_loc[Keys.LOCATION_TIME_KEY] # Duration of the activity, in milliseconds

        # User's preferred unit system.
        if logged_in:
            unit_system = self.user_mgr.retrieve_user_setting(logged_in_user_id, Keys.PREFERRED_UNITS_KEY)
        else:
            unit_system = Keys.UNITS_STANDARD_KEY

        # Get all the things.
        description_str = self.render_description_for_page(activity)
        name = App.render_activity_name(activity)
        activity_type = App.render_activity_type(activity)
        if activity_user_id is not None:
            ftp = self.user_mgr.estimate_ftp(activity_user_id)
        else:
            ftp = 0.0
        is_foot_based_activity = activity_type in Keys.FOOT_BASED_ACTIVITIES
        is_foot_based_activity_str = "false"
        if is_foot_based_activity:
            is_foot_based_activity_str = "true"

        # Retrieve cached summary data. If summary data has not been computed, then add this activity to the queue and move on without it.
        summary_data = self.data_mgr.retrieve_activity_summary(activity_id)
        if summary_data is None or len(summary_data) == 0:
            self.data_mgr.analyze_activity(activity, activity_user_id)

        # Start with the activity type.
        summary = "\t<li>" + activity_type + "</li>\n"

        # Add the location description.
        if summary_data is not None and Keys.ACTIVITY_LOCATION_DESCRIPTION_KEY in summary_data:
            location_description = summary_data[Keys.ACTIVITY_LOCATION_DESCRIPTION_KEY]
            if len(location_description) > 0:
                summary += "\t<li>" + App.render_array_reversed(location_description) + "</li>\n"

        # Add the activity date.
        if Keys.ACTIVITY_START_TIME_KEY in activity:
            summary += "\t<li>Start: <script>document.write(unix_time_to_local_string(" + str(activity[Keys.ACTIVITY_START_TIME_KEY]) + "))</script></li>\n"

        # Add the activity name.
        summary += "\t<li>Name: " + name + "</li>\n"

        # Build the detailed analysis table from data that was computed out-of-band and cached.
        details_str = ""
        splits_str = ""
        excluded_keys = Keys.UNSUMMARIZABLE_KEYS
        excluded_keys.append(Keys.LONGEST_DISTANCE)
        if summary_data is not None:
            for key in sorted(summary_data):
                if is_foot_based_activity and key == Keys.BEST_SPEED:
                    details_str += "<td><b>" + Keys.BEST_PACE + "</b></td><td>"
                    value = summary_data[key]
                    details_str += Units.convert_to_string_in_specified_unit_system(unit_system, value, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, Keys.BEST_PACE)
                    details_str += "</td><tr>\n"
                elif key == Keys.ACTIVITY_INTERVALS_KEY:
                    details_str += "<td><b>Intervals</b><td>"
                    details_str += App.render_intervals_str(summary_data[key])
                    details_str += "</td><tr>\n"
                elif key == Keys.KM_SPLITS:
                    if unit_system == Keys.UNITS_METRIC_KEY:
                        splits_str = "\t\t" + App.render_difference_array(summary_data[key])
                elif key == Keys.MILE_SPLITS:
                    if unit_system == Keys.UNITS_STANDARD_KEY:
                        splits_str = "\t\t" + App.render_difference_array(summary_data[key])
                elif key not in excluded_keys:
                    details_str += "<td><b>"
                    details_str += key
                    details_str += "</b></td><td>"
                    value = summary_data[key]
                    details_str += Units.convert_to_string_in_specified_unit_system(unit_system, value, Units.UNITS_DISTANCE_METERS, Units.UNITS_TIME_SECONDS, key)
                    details_str += "</td><tr>\n"
        if len(details_str) == 0:
            details_str = "<td><b>No data</b></td><tr>\n"

        # Append the hash (for debugging purposes).
        if self.debug:
            if summary_data is not None and Keys.ACTIVITY_HASH_KEY in summary_data:
                details_str += "<td><b>Activity Hash</b></td><td>"
                details_str += summary_data[Keys.ACTIVITY_HASH_KEY]
                details_str += "</td><tr>\n"

        # Controls are only allowed if the user viewing the activity owns it.
        if belongs_to_current_user:
            details_controls_str = "<td><button type=\"button\" onclick=\"return refresh_analysis()\">Refresh Analysis</button></td><tr>\n"
        else:
            details_controls_str = ""

        # List the tags.
        tags_str = self.render_tags(activity, activity_user_id, belongs_to_current_user)

        # List the comments.
        comments_str = self.render_comments(activity, logged_in)

        # List the export options.
        exports_title_str = ""
        exports_str = ""
        if logged_in:
            exports_title_str = "<h3>Export</h3>"
            exports_str = App.render_export_control(True, Keys.APP_ACCELEROMETER_KEY in activity)

        # List the edit controls.
        edit_title_str = ""
        edit_str = ""
        if belongs_to_current_user:
            edit_title_str = "<h3>Edit</h3>"
            edit_str = App.render_edit_controls()

        # Render the delete control.
        delete_str = ""
        if belongs_to_current_user:
            delete_str = App.render_delete_control()

        # Build the page title.
        if is_live:
            page_title = "Live Tracking"
        else:
            page_title = "Activity"

        # Was this a virtual activity in Zwift's Watopia?
        is_in_watopia = App.is_activity_in_zwift_watopia(activity_type, last_lat, last_lon)
        is_in_crit_city = App.is_activity_in_zwift_crit_city(activity_type, last_lat, last_lon)
        is_in_makuri_islands = App.is_activity_in_zwift_makuri_islands(activity_type, last_lat, last_lon)

        # If a google maps key was provided then use google maps, otherwise use open street map.
        if is_in_watopia and os.path.isfile(self.zwift_watopia_map_file) > 0:
            my_template = Template(filename=self.zwift_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, pagetitle=page_title, unit_system=unit_system, is_foot_based_activity=is_foot_based_activity_str, duration=duration, summary=summary, activityId=activity_id, userId=activity_user_id, ftp=ftp, description=description_str, details=details_str, details_controls=details_controls_str, tags=tags_str, comments=comments_str, exports_title=exports_title_str, exports=exports_str, edit_title=edit_title_str, edit=edit_str, delete=delete_str, splits=splits_str, map_file_name=ZWIFT_WATOPIA_MAP_FILE_NAME)
        elif is_in_crit_city and os.path.isfile(self.zwift_crit_city_map_file) > 0:
            my_template = Template(filename=self.zwift_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, pagetitle=page_title, unit_system=unit_system, is_foot_based_activity=is_foot_based_activity_str, duration=duration, summary=summary, activityId=activity_id, userId=activity_user_id, ftp=ftp, description=description_str, details=details_str, details_controls=details_controls_str, tags=tags_str, comments=comments_str, exports_title=exports_title_str, exports=exports_str, edit_title=edit_title_str, edit=edit_str, delete=delete_str, splits=splits_str, map_file_name=ZWIFT_CRIT_CITY_MAP_FILE_NAME)
        elif is_in_makuri_islands and os.path.isfile(self.zwift_makuri_islands_map_file) > 0:
            my_template = Template(filename=self.zwift_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, pagetitle=page_title, unit_system=unit_system, is_foot_based_activity=is_foot_based_activity_str, duration=duration, summary=summary, activityId=activity_id, userId=activity_user_id, ftp=ftp, description=description_str, details=details_str, details_controls=details_controls_str, tags=tags_str, comments=comments_str, exports_title=exports_title_str, exports=exports_str, edit_title=edit_title_str, edit=edit_str, delete=delete_str, splits=splits_str, map_file_name=ZWIFT_MAKURI_ISLANDS_MAP_FILE_NAME)
        elif self.google_maps_key:
            my_template = Template(filename=self.map_single_google_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, pagetitle=page_title, unit_system=unit_system, is_foot_based_activity=is_foot_based_activity_str, duration=duration, summary=summary, lastLat=last_lat, lastLon=last_lon, activityId=activity_id, userId=activity_user_id, ftp=ftp, description=description_str, details=details_str, details_controls=details_controls_str, tags=tags_str, comments=comments_str, exports_title=exports_title_str, exports=exports_str, edit_title=edit_title_str, edit=edit_str, delete=delete_str, splits=splits_str)
        else:
            my_template = Template(filename=self.map_single_osm_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, name=user_realname, pagetitle=page_title, unit_system=unit_system, is_foot_based_activity=is_foot_based_activity_str, duration=duration, summary=summary, lastLat=last_lat, lastLon=last_lon, activityId=activity_id, userId=activity_user_id, ftp=ftp, description=description_str, details=details_str, details_controls=details_controls_str, tags=tags_str, comments=comments_str, exports_title=exports_title_str, exports=exports_str, edit_title=edit_title_str, edit=edit_str, delete=delete_str, splits=splits_str)

    def render_page_for_activity(self, activity, user_realname, activity_user_id, logged_in_user_id, belongs_to_current_user, is_live):
        """Helper function for rendering the page corresonding to a specific activity."""

        try:
        
            # Does the activity contain any location data?
            if Keys.ACTIVITY_LOCATIONS_KEY in activity and len(activity[Keys.ACTIVITY_LOCATIONS_KEY]) > 0:
                return self.render_page_for_mapped_activity(user_realname, activity[Keys.ACTIVITY_ID_KEY], activity, activity_user_id, logged_in_user_id, belongs_to_current_user, is_live)

            # Does the activity contain accelerometer data, as with lifting activities recorded from the companion app?
            elif Keys.APP_ACCELEROMETER_KEY in activity or Keys.APP_SETS_KEY in activity:
                return self.render_page_for_unmapped_activity(user_realname, activity[Keys.ACTIVITY_ID_KEY], activity, activity_user_id, logged_in_user_id, belongs_to_current_user, is_live)

            # Does the activity contain any sensor data at all, if so then we can still render something?
            elif any(x in activity for x in Keys.SENSOR_KEYS):
                return self.render_page_for_unmapped_activity(user_realname, activity[Keys.ACTIVITY_ID_KEY], activity, activity_user_id, logged_in_user_id, belongs_to_current_user, is_live)

            # No idea what to do with this.
            else:
                return self.render_page_for_errored_activity(activity[Keys.ACTIVITY_ID_KEY], logged_in_user_id is not None, belongs_to_current_user)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + App.activity.__name__)
        return self.render_error()

    def render_page_for_multiple_mapped_activities(self, email, user_realname, device_id_strs, user_id, logged_in):
        """Helper function for rendering the map to track multiple devices."""

        if device_id_strs is None:
            my_template = Template(filename=self.error_logged_in_html_file, module_directory=self.tempmod_dir)
            return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, error="No device IDs were specified.")

        last_lat = 0.0
        last_lon = 0.0

        for device_id_str in device_id_strs:
            activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_id_str)
            if activity_id is None:
                continue

            locations = self.data_mgr.retrieve_activity_locations(activity_id)
            if locations is None:
                continue

            if len(locations) > 0:
                last_loc = locations[-1]

                last_lat = last_loc[Keys.LOCATION_LAT_KEY]
                last_lon = last_loc[Keys.LOCATION_LON_KEY]

        my_template = Template(filename=self.map_multi_html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(logged_in), product=PRODUCT_NAME, root_url=self.root_url, email=email, name=user_realname, lastLat=last_lat, lastLon=last_lon, userId=str(user_id))

    def render_error(self, error_str=None):
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

    def render_page_not_found(self):
        """Renders the 404 error page."""
        try:
            error_html_file = os.path.join(self.root_dir, HTML_DIR, 'error_404.html')
            my_template = Template(filename=error_html_file, module_directory=self.tempmod_dir)
            return my_template.render(product=PRODUCT_NAME, root_url=self.root_url)
        except:
            pass
        return ""

    @Perf.statistics
    def live_activity(self, activity, activity_user):
        """Renders the map page for the specified (in progress) activity."""

        # Get the logged in user (if any).
        logged_in_user_id = None
        logged_in_username = self.user_mgr.get_logged_in_user()
        if logged_in_username is not None:
            logged_in_user_id, _, _ = self.user_mgr.retrieve_user(logged_in_username)

        # Is the activity still live? After one day, the activity is no longer considered live.
        end_time = self.data_mgr.compute_activity_end_time(activity) / 1000
        now = time.time()
        diff = now - end_time
        diff_hours = diff / 60 / 60
        diff_days = diff_hours / 24
        if diff_days >= 1.0:
            return self.render_error("The user has not posted any data in over 24 hours.")

        # Determine if the current user can view the activity.
        activity_user_id = activity_user[Keys.DATABASE_ID_KEY]
        belongs_to_current_user = str(activity_user_id) == str(logged_in_user_id)
        if not (self.data_mgr.is_activity_public(activity) or belongs_to_current_user):
            return self.render_error("The requested activity is not public.")

        # Render from template.
        return self.render_page_for_activity(activity, activity_user[Keys.REALNAME_KEY], activity_user_id, logged_in_user_id, belongs_to_current_user, True)

    @Perf.statistics
    def live_device(self, device_str):
        """Renders the map page for the current activity from a single device."""

        # Determine the ID of the most recent activity logged from the specified device.
        activity = self.data_mgr.retrieve_most_recent_activity_for_device(device_str)
        if activity is None:
            return self.render_error()

        # Determine who owns the device.
        device_user = self.user_mgr.retrieve_user_from_device(device_str)

        # Render the page.
        return self.live_activity(activity, device_user)

    @Perf.statistics
    def live_user(self, user_str):
        """Renders the map page for the current activity for a given user."""

        # Look up the user.
        user = self.user_mgr.retrieve_user_details(user_str)

        # Find the user's most recent activity.
        user_id = str(user[Keys.DATABASE_ID_KEY])
        user_devices = self.user_mgr.retrieve_user_devices(user_id)
        activity = self.data_mgr.retrieve_most_recent_activity_for_user(user_devices)
        if activity is None:
            return self.render_error()

        # Render the page.
        return self.live_activity(activity, user)

    @Perf.statistics
    def activity(self, activity_id):
        """Renders the details page for an activity."""

        # Sanity check the activity ID.
        if not InputChecker.is_uuid(activity_id):
            return self.render_error("Invalid activity ID")

        # Get the logged in user (if any).
        logged_in_user_id = None
        logged_in_username = self.user_mgr.get_logged_in_user()
        if logged_in_username is not None:
            logged_in_user_id, _, _ = self.user_mgr.retrieve_user(logged_in_username)

        # Load the activity.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if activity is None:
            return self.render_error("The requested activity does not exist.")

        # Determine who owns the device, and hence the activity.
        activity_user_id, activity_username, activity_user_realname = self.user_mgr.get_activity_user(activity)
        belongs_to_current_user = str(activity_user_id) == str(logged_in_user_id)
        if activity_user_realname is None:
            activity_user_realname = ""

        # Determine if the current user can view the activity.
        if not (self.data_mgr.is_activity_public(activity) or belongs_to_current_user):
            return self.render_error("The requested activity is not public.")

        # Render from template.
        return self.render_page_for_activity(activity, activity_user_realname, activity_user_id, logged_in_user_id, belongs_to_current_user, False)

    @Perf.statistics
    def edit_activity(self, activity_id):
        """Renders the edit page for an activity."""

        # Sanity check the activity ID.
        if not InputChecker.is_uuid(activity_id):
            return self.render_error("Invalid activity ID")

        # Get the logged in user.
        username = self.user_mgr.get_logged_in_user()
        if username is None:
            raise RedirectException(LOGIN_URL)

        # Get the details of the logged in user.
        user_id, _, user_realname = self.user_mgr.retrieve_user(username)
        if user_id is None:
            self.log_error('Unknown user ID')
            raise RedirectException(LOGIN_URL)

        # Load the activity.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if activity is None:
            return self.render_error("The requested activity does not exist.")

        # Determine who owns the device, and hence the activity.
        activity_user_id, _, _ = self.user_mgr.get_activity_user(activity)
        belongs_to_current_user = str(activity_user_id) == str(user_id)
        if not belongs_to_current_user:
            return self.render_error("The logged in user does not own the requested activity.")

        # Render the activity name.
        activity_name_str = ""
        if Keys.ACTIVITY_NAME_KEY in activity:
            activity_name_str = activity[Keys.ACTIVITY_NAME_KEY]

        # Render the activity type.
        activity_type_str = ""
        if Keys.ACTIVITY_TYPE_KEY in activity:
            activity_type_str = activity[Keys.ACTIVITY_TYPE_KEY]

        # Render the activity description.
        description_str = ""
        if Keys.ACTIVITY_DESCRIPTION_KEY in activity:
            description_str = activity[Keys.ACTIVITY_DESCRIPTION_KEY]

        # Render from template.
        html_file = os.path.join(self.root_dir, HTML_DIR, 'edit_activity.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, activity_id=activity_id, activity_name=activity_name_str, activity_type=activity_type_str, description=description_str)

    @Perf.statistics
    def add_photos(self, activity_id):
        """Renders the edit page for an activity."""

        # Sanity check the activity ID.
        if not InputChecker.is_uuid(activity_id):
            return self.render_error("Invalid activity ID")

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
        html_file = os.path.join(self.root_dir, HTML_DIR, 'add_photos.html')
        my_template = Template(filename=html_file, module_directory=self.tempmod_dir)
        return my_template.render(nav=self.create_navbar(True), product=PRODUCT_NAME, root_url=self.root_url, email=username, name=user_realname, activity_id=activity_id)

    @Perf.statistics
    def device(self, device_str):
        """Renders the map page for a single device."""

        # Get the logged in user (if any).
        logged_in_user_id = None
        logged_in_username = self.user_mgr.get_logged_in_user()
        if logged_in_username is not None:
            logged_in_user_id, _, _ = self.user_mgr.retrieve_user(logged_in_username)

        # Get the activity ID being requested. If one is not provided then get the latest activity for the device
        activity_id = self.data_mgr.retrieve_most_recent_activity_id_for_device(device_str)
        if activity_id is None:
            return self.render_error()

        # Determine who owns the device.
        device_user = self.user_mgr.retrieve_user_from_device(device_str)
        activity_user_id = device_user[Keys.DATABASE_ID_KEY]
        belongs_to_current_user = str(activity_user_id) == str(logged_in_user_id)

        # Load the activity.
        activity = self.data_mgr.retrieve_activity(activity_id)
        if activity is None:
            return self.render_error("The requested activity does not exist.")

        # Determine if the current user can view the activity.
        if not (self.data_mgr.is_activity_public(activity) or belongs_to_current_user):
            return self.render_error("The requested activity is not public.")

        # Render from template.
        return self.render_page_for_activity(activity, device_user[Keys.REALNAME_KEY], activity_user_id, logged_in_user_id, belongs_to_current_user, False)

    @Perf.statistics
    def my_activities(self):
        """Renders the list of the specified user's activities."""
        return self.render_simple_page('my_activities.html')

    @Perf.statistics
    def all_activities(self):
        """Renders the list of all activities the specified user is allowed to view."""
        return self.render_simple_page('all_activities.html')

    @Perf.statistics
    def record_progression(self, activity_type, record_name):
        """Renders the list of records, in order of progression, for the specified user and record type."""
        kwargs = {"activity_type" : activity_type, "record_name" : record_name} 
        return self.render_simple_page('records.html', **kwargs)

    @Perf.statistics
    def workouts(self):
        """Renders the workouts view."""
        return self.render_simple_page('workouts.html')

    @Perf.statistics
    def workout(self, workout_id):
        """Renders the view for an individual workout."""

        # Sanity check the input.
        if workout_id is None:
            return self.render_error()
        if not InputChecker.is_uuid(workout_id):
            return self.render_error()

        # Render from template.
        kwargs = {"workout_id" : workout_id} 
        return self.render_simple_page('workout.html', **kwargs)

    @Perf.statistics
    def user_stats(self):
        """Renders the user's statistics view."""
        return self.render_simple_page('statistics.html')

    @Perf.statistics
    def gear(self):
        """Renders the list of all gear belonging to the logged in user."""
        return self.render_simple_page('gear.html')

    @Perf.statistics
    def service_history(self, gear_id):
        """Renders the service history for a particular piece of gear."""

        # Sanity check the input.
        if gear_id is None:
            return self.render_error()
        if not InputChecker.is_uuid(gear_id):
            return self.render_error()

        # Render from template.
        kwargs = {"gear_id" : gear_id} 
        return self.render_simple_page('service_history.html', **kwargs)

    @Perf.statistics
    def friends(self):
        """Renders the list of users who are friends with the logged in user."""
        return self.render_simple_page('friends.html')

    @Perf.statistics
    def device_list(self):
        """Renders the list of a user's devices."""
        return self.render_simple_page('device_list.html')

    @Perf.statistics
    def manual_entry(self, activity_type):
        """Called when the user selects an activity type, indicatig they want to make a manual data entry."""
        print(activity_type)

    @Perf.statistics
    def import_activity(self):
        """Renders the import page."""

        # Build the list options for manual entry.
        activity_type_list = self.data_mgr.retrieve_activity_types()
        activity_type_list_str = "\t\t\t<option value=\"-\">-</option>\n"
        for activity_type in activity_type_list:
            activity_type_list_str += "\t\t\t<option value=\"" + activity_type + "\">" + activity_type + "</option>\n"

        # Render from template.
        kwargs = {"activity_type_list" : activity_type_list_str} 
        return self.render_simple_page('import.html', **kwargs)

    @Perf.statistics
    def pace_plans(self):
        """Renders the pace plans page."""
        return self.render_simple_page('pace_plans.html')

    @Perf.statistics
    def task_status(self):
        """Renders the status page for deferred tasks, such as file imports and activity analysis."""
        return self.render_simple_page('task_status.html')

    @Perf.statistics
    def profile(self):
        """Renders the user's profile page."""
        return self.render_simple_page('profile.html')

    @Perf.statistics
    def settings(self):
        """Renders the user's settings page."""
        return self.render_simple_page('settings.html')

    @Perf.statistics
    def ical(self, calendar_id):
        """Returns the ical calendar with the specified ID."""
        if calendar_id is None:
            return self.render_error()
        if not InputChecker.is_uuid(calendar_id):
            return self.render_error()

        handled, response = self.ical_server.handle_request(calendar_id)
        return handled, response

    @Perf.statistics
    def api(self, user_id, verb, method, params):
        """Handles an API request."""
        api = Api.Api(self.user_mgr, self.data_mgr, user_id, self.root_url)
        handled, response = api.handle_api_1_0_request(verb, method, params)
        return handled, response

    @Perf.statistics
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

    @Perf.statistics
    def create_login(self):
        """Renders the create login page."""
        create_login_html_file = os.path.join(self.root_dir, HTML_DIR, 'create_login.html')
        my_template = Template(filename=create_login_html_file, module_directory=self.tempmod_dir)
        return my_template.render(product=PRODUCT_NAME, root_url=self.root_url)

    @Perf.statistics
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

    @Perf.statistics
    def about(self):
        """Renders the about page."""
        return self.render_simple_page('about.html')

    @Perf.statistics
    def status(self):
        """Renders the status page. Used as a simple way to tell if the site is up."""
        return "Up"

    @Perf.statistics
    def api_keys(self):
        """Renders the api key management page."""
        return self.render_simple_page('api_keys.html')
