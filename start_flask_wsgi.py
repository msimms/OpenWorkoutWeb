#! /usr/bin/env python
# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2022 Michael J Simms
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

import argparse
import signal
import logging
import os
import sys
import traceback

import App
import AppFactory
import Config
import DatabaseException

g_app = None

def signal_handler(signal, frame):
    global g_app

    print("Exiting...")
    if g_app is not None:
        g_app.terminate()
    sys.exit(0)

def log_error(log_str):
    """Writes an error message to the log file."""
    logger = logging.getLogger()
    logger.error(log_str)

def error(env, start_response):
    """Renders the error page."""
    content = g_app.render_error().encode('utf-8')
    start_response('500', [('Content-Type', 'text/html')])
    return [content]

def stats(env, start_response):
    """Renders the internal statistics page."""
    try:
        content = g_app.stats().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + stats.__name__)
    return error(env, start_response)

def live(env, start_response):
    """Renders the map page for the current activity from a single device."""
    try:
        content = g_app.live().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + live.__name__)
    return error(env, start_response)

def live_user(env, start_response):
    """Renders the map page for the current activity from a specified user."""
    try:
        content = g_app.live_user().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + live_user.__name__)
    return error(env, start_response)

def activity(env, start_response):
    """Renders the details page for an activity."""
    try:
        content = g_app.activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + activity.__name__)
    return error(env, start_response)

def edit_activity(env, start_response):
    """Renders the edit page for an activity."""
    try:
        content = g_app.edit_activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + edit_activity.__name__)
    return error(env, start_response)

def trim_activity(env, start_response):
    """Renders the trim page for an activity."""
    try:
        content = g_app.trim_activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + trim_activity.__name__)
    return error(env, start_response)

def merge_activity(env, start_response):
    """Renders the merge page for an activity."""
    try:
        content = g_app.merge_activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + merge_activity.__name__)
    return error(env, start_response)

def add_photos(env, start_response):
    """Renders the add photos page for an activity."""
    try:
        content = g_app.add_photos().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + add_photos.__name__)
    return error(env, start_response)

def device(env, start_response):
    """Renders the map page for a single device."""
    try:
        content = g_app.device().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + device.__name__)
    return error(env, start_response)

def my_activities(env, start_response):
    """Renders the list of the specified user's activities."""
    try:
        content = g_app.my_activities().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + my_activities.__name__)
    return error(env, start_response)

def all_activities(env, start_response):
    """Renders the list of all activities the specified user is allowed to view."""
    try:
        content = g_app.all_activities().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + all_activities.__name__)
    return error(env, start_response)

def record_progression(env, start_response):
    """Renders the list of records, in order of progression, for the specified user and record type."""
    try:
        content = g_app.record_progression().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + record_progression.__name__)
    return error(env, start_response)

def workouts(env, start_response):
    """Renders the workouts view."""
    try:
        content = g_app.workouts().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + workouts.__name__)
    return error(env, start_response)

def workout(env, start_response):
    """Renders the view for an individual workout."""
    try:
        content = g_app.workout().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + workout.__name__)
    return error(env, start_response)

def statistics(env, start_response):
    """Renders the statistics view."""
    try:
        content = g_app.statistics().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + statistics.__name__)
    return error(env, start_response)

def gear(env, start_response):
    """Renders the list of all gear belonging to the logged in user."""
    try:
        content = g_app.gear().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + gear.__name__)
    return error(env, start_response)

def service_history(env, start_response):
    """Renders the service history for a particular piece of gear."""
    try:
        content = g_app.service_history().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + service_history.__name__)
    return error(env, start_response)

def friends(env, start_response):
    """Renders the list of users who are friends with the logged in user."""
    try:
        content = g_app.friends().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + friends.__name__)
    return error(env, start_response)

def device_list(env, start_response):
    """Renders the list of a user's devices."""
    try:
        content = g_app.device_list().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + device_list.__name__)
    return error(env, start_response)

def manual_entry(env, start_response):
    """Called when the user selects an activity type, indicating they want to make a manual data entry."""
    try:
        content = g_app.manual_entry().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + manual_entry.__name__)
    return error(env, start_response)

def import_activity(env, start_response):
    """Renders the import page."""
    try:
        content = g_app.import_activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + import_activity.__name__)
    return error(env, start_response)

def add_pace_plan(env, start_response):
    """Renders the pace plans page."""
    try:
        content = g_app.add_pace_plan().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + add_pace_plan.__name__)
    return error(env, start_response)

def pace_plans(env, start_response):
    """Renders the pace plans page."""
    try:
        content = g_app.pace_plans().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + pace_plans.__name__)
    return error(env, start_response)

def task_status(env, start_response):
    """Renders the import status page."""
    try:
        content = g_app.task_status().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + task_status.__name__)
    return error(env, start_response)

def profile(env, start_response):
    """Renders the user's profile page."""
    try:
        content = g_app.profile().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + profile.__name__)
    return error(env, start_response)

def settings(env, start_response):
    """Renders the user's settings page."""
    try:
        content = g_app.settings().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + settings.__name__)
    return error(env, start_response)

def login(env, start_response):
    """Renders the login page."""
    try:
        content = g_app.login().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error('Unhandled exception in ' + settings.__name__)
    return error(env, start_response)

def create_login(env, start_response):
    """Renders the create login page."""
    try:
        content = g_app.create_login().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except:
        g_app.log_error('Unhandled exception in ' + create_login.__name__)
    return error(env, start_response)

def logout(env, start_response):
    """Ends the logged in session."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return error(env, start_response)

def about(env, start_response):
    """Renders the about page."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return error(env, start_response)

def status(env, start_response):
    """Renders the status page. Used as a simple way to tell if the site is up."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return error(env, start_response)

def ical(env, start_response):
    """Returns the ical calendar with the specified ID."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return error(env, start_response)

def api_keys(env, start_response):
    """Renders the api key management page."""
    try:
        content = g_app.api_keys().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + api_keys.__name__)
    return error(env, start_response)

def admin(env, start_response):
    """Renders the admin page."""
    try:
        content = g_app.admin().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + admin.__name__)
    return error(env, start_response)

def api(env, start_response):
    """Endpoint for API calls."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return error(env, start_response)

def google_maps(env, start_response):
    """Returns the Google Maps API key."""
    global g_app
    start_response('302 Found', [('Location', 'https://maps.googleapis.com/maps/api/js?key=' + g_app.google_maps_key)])
    return []

def index(env, start_response):
    """Renders the index page."""
    return login(env, start_response)

def main():
    """Entry point for the flask+wsgi version of the app."""
    global g_app

    # Make sure we have a compatible version of python.
    if sys.version_info[0] < 3:
        print("This application requires python 3.")
        sys.exit(1)

    # Parse the command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, action="store", default="", help="The configuration file.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    try:
        # Load the config file.
        config = Config.Config()
        if len(args.config) > 0:
            config.load(args.config)

        # Register the signal handler.
        signal.signal(signal.SIGINT, signal_handler)

        # Create all the objects that actually implement the functionality.
        root_dir = os.path.dirname(os.path.abspath(__file__))
        g_app = AppFactory.create_flask(config, root_dir)
    except DatabaseException.DatabaseException as e:
        print(e.message)
        sys.exit(1)

if __name__ == "__main__":
    main()
