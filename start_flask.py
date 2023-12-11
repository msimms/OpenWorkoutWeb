# Copyright 2018 Michael J Simms
"""Main application - if using flask, contains all web page handlers"""

import argparse
import functools
import json
import os
import signal
import sys
import traceback
import flask

import App
import ApiException
import AppFactory
import Config
import DatabaseException
import Dirs
import Keys
import SessionException

PHOTOS_DIR = 'photos'

g_flask_app = flask.Flask(__name__)
g_flask_app.secret_key = 'UB2s60qJrithXHt2w71f'
g_flask_app.url_map.strict_slashes = False
g_app = None

def signal_handler(signal, frame):
    global g_app

    print("Exiting...")
    if g_app is not None:
        g_app.terminate()
    sys.exit(0)

def login_required(function_to_protect):
    @functools.wraps(function_to_protect)
    def wrapper(*args, **kwargs):
        global g_app
        user = g_app.user_mgr.session_mgr.get_logged_in_username()
        if user:
            return function_to_protect(*args, **kwargs)
        return flask.redirect(flask.url_for('login'))
    return wrapper

@g_flask_app.errorhandler(404)
def page_not_found(e):
    global g_app
    return g_app.error_404(None, None, None, None)

@g_flask_app.route('/css/<file_name>')
def css(file_name):
    """Returns the CSS page."""
    try:
        return flask.send_from_directory(Dirs.CSS_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + css.__name__)
    return g_app.render_error()

@g_flask_app.route('/data/<file_name>')
def data(file_name):
    """Returns the data page."""
    try:
        return flask.send_from_directory(Dirs.DATA_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + data.__name__)
    return g_app.render_error()

@g_flask_app.route('/js/<file_name>')
def js(file_name):
    """Returns the JS page."""
    try:
        return flask.send_from_directory(Dirs.JS_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + js.__name__)
    return g_app.render_error()

@g_flask_app.route('/images/<file_name>')
def images(file_name):
    """Returns images."""
    try:
        return flask.send_from_directory(Dirs.IMAGES_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + images.__name__)
    return g_app.render_error()

@g_flask_app.route('/media/<file_name>')
def media(file_name):
    """Returns media files (icons, etc.)."""
    try:
        return flask.send_from_directory(Dirs.MEDIA_DIR, file_name)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + media.__name__)
    return g_app.render_error()

@g_flask_app.route('/photos/<user_id>/<file_name>')
def photos(user_id, file_name):
    """Returns an activity photo."""
    try:
        return flask.send_from_directory(Dirs.PHOTOS_DIR, os.path.join(user_id, file_name))
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + photos.__name__)
    return g_app.render_error()

@g_flask_app.route('/error')
def error(error_str=None):
    """Renders the error page."""
    try:
        return g_app.render_error(error_str)
    except:
        pass
    return g_app.render_error()

@g_flask_app.route('/stats')
@login_required
def stats():
    """Renders the internal statistics page."""
    try:
        return g_app.performance_stats()
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + stats.__name__)
    return error()

@g_flask_app.route('/live/<device_str>')
def live(device_str):
    """Renders the map page for the current activity from a single device."""
    try:
        return g_app.live(device_str)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + live.__name__)
    return error()

@g_flask_app.route('/live_user/<user_str>')
def live_user(user_str):
    """Renders the map page for the current activity from a specified user."""
    try:
        return g_app.live_user(user_str)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + live_user.__name__)
    return error()

@g_flask_app.route('/activity/<activity_id>')
def activity(activity_id):
    """Renders the details page for an activity."""
    try:
        return g_app.activity(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + activity.__name__)
    return error()

@g_flask_app.route('/edit_activity/<activity_id>')
@login_required
def edit_activity(activity_id):
    """Renders the edit page for an activity."""
    global g_app
    try:
        return g_app.edit_activity(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + edit_activity.__name__)
    return error()

@g_flask_app.route('/trim_activity/<activity_id>')
@login_required
def trim_activity(activity_id):
    """Renders the trim page for an activity."""
    global g_app
    try:
        return g_app.trim_activity(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + trim_activity.__name__)
    return error()

@g_flask_app.route('/merge_activity/<activity_id>')
@login_required
def merge_activity(activity_id):
    """Renders the merge page for an activity."""
    global g_app
    try:
        return g_app.merge_activity(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + merge_activity.__name__)
    return error()

@g_flask_app.route('/add_photos/<activity_id>')
@login_required
def add_photos(activity_id):
    """Renders the add photos page for an activity."""
    global g_app
    try:
        return g_app.add_photos(activity_id)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + add_photos.__name__)
    return error()

@g_flask_app.route('/device/<device_str>')
def device(device_str):
    """Renders the map page for a single device."""
    global g_app
    try:
        return g_app.device(device_str)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + device.__name__)
    return error()

@g_flask_app.route('/my_activities')
@login_required
def my_activities():
    """Renders the list of the specified user's activities."""
    global g_app
    try:
        return g_app.my_activities()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + my_activities.__name__)
    return error()

@g_flask_app.route('/all_activities')
@login_required
def all_activities():
    """Renders the list of all activities the specified user is allowed to view."""
    global g_app
    try:
        return g_app.all_activities()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + all_activities.__name__)
    return error()

@g_flask_app.route('/record_progression/<activity_type>/<record_name>')
@login_required
def record_progression(activity_type, record_name):
    """Renders the list of records, in order of progression, for the specified user and record type."""
    global g_app
    try:
        return g_app.record_progression(activity_type, record_name)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + record_progression.__name__)
    return error()

@g_flask_app.route('/workouts')
@login_required
def workouts():
    """Renders the workouts view."""
    global g_app
    try:
        return g_app.workouts()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + workouts.__name__)
    return error()

@g_flask_app.route('/workout/<workout_id>')
@login_required
def workout(workout_id):
    """Renders the view for an individual workout."""
    global g_app
    try:
        return g_app.workout(workout_id)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + workout.__name__)
    return error()

@g_flask_app.route('/statistics')
@login_required
def statistics():
    """Renders the statistics view."""
    global g_app
    try:
        return g_app.user_stats()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + statistics.__name__)
    return error()

@g_flask_app.route('/gear')
@login_required
def gear():
    """Renders the list of all gear belonging to the logged in user."""
    global g_app
    try:
        return g_app.gear()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + gear.__name__)
    return error()

@g_flask_app.route('/service_history/<gear_id>')
@login_required
def service_history(gear_id):
    """Renders the service history for a particular piece of gear."""
    global g_app
    try:
        return g_app.service_history(gear_id)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + service_history.__name__)
    return error()

@g_flask_app.route('/friends')
@login_required
def friends():
    """Renders the list of users who are friends with the logged in user."""
    global g_app
    try:
        return g_app.friends()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + friends.__name__)
    return error()

@g_flask_app.route('/device_list')
@login_required
def device_list():
    """Renders the list of a user's devices."""
    global g_app
    try:
        return g_app.device_list()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + device_list.__name__)
    return error()

@g_flask_app.route('/manual_entry/<activity_type>')
@login_required
def manual_entry(activity_type):
    """Called when the user selects an activity type, indicating they want to make a manual data entry."""
    global g_app
    try:
        return g_app.manual_entry(activity_type)
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + manual_entry.__name__)
    return error()

@g_flask_app.route('/import_activity')
@login_required
def import_activity():
    """Renders the import page."""
    global g_app
    try:
        return g_app.import_activity()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + import_activity.__name__)
    return error()

@g_flask_app.route('/add_pace_plan')
@login_required
def add_pace_plan():
    """Renders the pace plans page."""
    global g_app
    try:
        return g_app.add_pace_plan()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + add_pace_plan.__name__)
    return error()

@g_flask_app.route('/pace_plans')
@login_required
def pace_plans():
    """Renders the pace plans page."""
    global g_app
    try:
        return g_app.pace_plans()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + pace_plans.__name__)
    return error()

@g_flask_app.route('/task_status')
@login_required
def task_status():
    """Renders the import status page."""
    global g_app
    try:
        return g_app.task_status()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + task_status.__name__)
    return error()

@g_flask_app.route('/profile')
@login_required
def profile():
    """Renders the user's profile page."""
    global g_app
    try:
        return g_app.profile()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + profile.__name__)
    return error()

@g_flask_app.route('/settings')
@login_required
def settings():
    """Renders the user's settings page."""
    global g_app
    try:
        return g_app.settings()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error(traceback.format_exc())
        g_app.log_error(sys.exc_info()[0])
        g_app.log_error('Unhandled exception in ' + settings.__name__)
    return error()

@g_flask_app.route('/login')
def login():
    """Renders the login page."""
    global g_app
    try:
        return g_app.login()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except:
        g_app.log_error('Unhandled exception in ' + login.__name__)
    return error()

@g_flask_app.route('/create_login')
def create_login():
    """Renders the create login page."""
    global g_app
    try:
        return g_app.create_login()
    except:
        g_app.log_error('Unhandled exception in ' + g_flask_app.__name__)
    return error()

@g_flask_app.route('/logout')
def logout():
    """Ends the logged in session."""
    global g_app
    try:
        return g_app.logout()
    except App.RedirectException as e:
        return flask.redirect(e.url, code=302)
    except SessionException.SessionTerminatedException as e:
        response = flask.redirect(e.url, code=302)
        response.set_cookie(Keys.SESSION_KEY, '', expires=0)
        return response
    return g_app.render_error()

@g_flask_app.route('/about')
def about():
    """Renders the about page."""
    global g_app
    result = ""
    try:
        result = g_app.about()
    except:
        result = g_app.render_error()
    return result

@g_flask_app.route('/status')
def status():
    """Renders the status page. Used as a simple way to tell if the site is up."""
    global g_app
    result = ""
    try:
        result = g_app.status()
    except:
        result = g_app.render_error()
    return result

@g_flask_app.route('/ical/<calendar_id>')
def ical(calendar_id):
    """Returns the ical calendar with the specified ID."""
    global g_app
    result = ""
    try:
        _, response = g_app.ical(calendar_id)
        return response
    except:
        result = g_app.render_error()
    return result

@g_flask_app.route('/api_keys')
@login_required
def api_keys():
    """Renders the api key management page."""
    global g_app
    result = ""
    try:
        result = g_app.api_keys()
    except:
        result = g_app.error()
    return result

@g_flask_app.route('/admin')
@login_required
def admin():
    """Renders the admin page."""
    global g_app
    result = ""
    try:
        result = g_app.admin()
    except:
        result = g_app.error()
    return result

@g_flask_app.route('/api/<version>/<method>', methods = ['GET','POST','DELETE'])
def api(version, method):
    """Endpoint for API calls."""
    global g_app
    response = ""
    code = 500
    try:
        # The the API params.
        if flask.request.method == 'GET':
            verb = "GET"
            params = flask.request.args
        elif flask.request.method == 'DELETE':
            verb = "DELETE"
            params = flask.request.args
        elif flask.request.data:
            verb = "POST"
            params = json.loads(flask.request.data)
        else:
            verb = "GET"
            params = ""

        # Get the logged in user, or lookup the user using the API key.
        user_id = None
        if Keys.API_KEY in params:

            # API key.
            api_key = params[Keys.API_KEY]

            # Which user is associated with this key?
            user_id, _, _, max_rate = g_app.user_mgr.retrieve_user_from_api_key(api_key)
            if user_id is not None:

                # Make sure the key is not being abused.
                if not g_app.data_mgr.check_api_rate(api_key, max_rate):
                    user_id = None
                    code = 429
                    response = "Excessive API requests."
                    g_app.log_error(response)
        else:

            # API key not provided, check the session key.
            username = g_app.user_mgr.get_logged_in_username()
            if username is not None:
                user_id, _, _ = g_app.user_mgr.retrieve_user(username)

        # Process the API request.
        if version == '1.0':
            handled, response = g_app.api(user_id, verb, method, params)
            if not handled:
                response = "Failed to handle request: " + str(method)
                g_app.log_error(response)
                code = 400
            else:
                code = 200
        else:
            g_app.log_error("Failed to handle request for api version " + version)
            code = 400
    except ApiException.ApiException as e:
        g_app.log_error(e.message)
        code = e.code
    except SessionException.SessionTerminatedException as e:
        response = g_app.make_response("")
        response.set_cookie(Keys.SESSION_KEY, '', expires=0)
        response.delete_cookie(Keys.SESSION_KEY)
        return response
    except Exception as e:
        response = str(e.args[0])
        g_app.log_error(response)
        code = 500
    except:
        code = 500
    return response, code

@g_flask_app.route('/google_maps')
def google_maps():
    """Returns the Google Maps API key."""
    return flask.redirect("https://maps.googleapis.com/maps/api/js?key=" + g_app.google_maps_key, code=302)

@g_flask_app.route('/')
def index():
    """Renders the index page."""
    return login()

def main():
    """Entry point for the flask version of the app."""
    global g_app
    global g_flask_app

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
        g_flask_app.run(host=config.get_bindname(), port=config.get_bindport(), debug=config.is_debug_enabled())
    except DatabaseException.DatabaseException as e:
        print(e.message)
        sys.exit(1)

if __name__ == '__main__':
    main()
