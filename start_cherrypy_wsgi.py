# Copyright 2022 Michael J Simms

import argparse
import cherrypy
import json
import logging
import os
import signal
import sys
import traceback

import ApiException
import App
import AppFactory
import CherryPyFrontEnd
import Config
import DatabaseException
import Dirs
import InputChecker
import SessionMgr

from urllib.parse import parse_qs

SESSION_COOKIE = 'session_cookie'

g_front_end = None
g_session_mgr = None

def signal_handler(signal, frame):
    global g_front_end

    print("Exiting...")
    if g_front_end is not None:
        g_front_end.terminate()
    sys.exit(0)

@cherrypy.tools.register('before_finalize', priority=60)
def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://*.googleapis.com;"\
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://*.googleapis.com https://maps.gstatic.com;"\
        "object-src 'self';"\
        "font-src 'self' https://fonts.gstatic.com;"\
        "style-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://*.googleapis.com;"\
        "img-src 'self' *;"

def get_verb_path_params_and_cookie(env):
    """Gets all the thigns we need from an HTTP request."""

    verb = env['REQUEST_METHOD']
    path = env['REQUEST_URI'].split('/')[2:] # Don't need the first part of the path
    params = {}
    cookie = None

    # Look for our custom session cookie.
    if 'HTTP_COOKIE' in env:
        cookie_list_str = env['HTTP_COOKIE']
        cookie_list = cookie_list_str.split('; ')
        for temp_cookie in cookie_list:
            cookie_index = temp_cookie.find(SESSION_COOKIE)
            if cookie_index == 0:
                cookie = temp_cookie[len(SESSION_COOKIE) + 1:]

    # Parse the path and read any params.
    num_path_elems = len(path)
    if num_path_elems > 0:

        # GET requests will have the parameters in the URL.
        if verb == 'GET' or verb == 'DELETE':

            # Split off the params from a GET request.
            method_and_params = path[num_path_elems - 1].split('?')
            path[num_path_elems - 1] = method_and_params[0]

            # Did we find any parameters?
            if len(method_and_params) > 1:
                temp_params = parse_qs(method_and_params[1])
                for k in temp_params:
                    params[k] = (temp_params[k])[0]

        # POST requests will have the parameters in the body.
        elif verb == 'POST':
            temp_params = env['wsgi.input'].read()
            if len(temp_params) > 0:
                params = json.loads(temp_params)

    return verb, path, params, cookie

def do_auth_check(f):
    """Function decorator for endpoints that require the user to be logged in."""

    def auth_check(*args, **kwargs):
        global g_session_mgr

        # Extract the things we need from the request.
        env = args[0]
        _, _, _, cookie = get_verb_path_params_and_cookie(env)
        if g_session_mgr.get_logged_in_username_from_cookie(cookie) is not None:

            # User had a valid session token, so set it, do the request, and clear.
            g_session_mgr.set_current_session(cookie)
            response = f(*args, **kwargs)
            g_session_mgr.clear_current_session()

        # User does not have a valid session token, redirect to the login page.
        else:
            global g_front_end

            start_response = args[1]
            content = g_front_end.backend.login()
            start_response('401 Unauthorized', [])
            response = [content.encode('utf-8')]
 
        return response

    return auth_check

def do_session_check(f):
    """Function decorator for endpoints that where logging in is optional."""

    def session_check(*args, **kwargs):
        global g_session_mgr

        # Extract the things we need from the request.
        env = args[0]
        _, _, _, cookie = get_verb_path_params_and_cookie(env)

        # User had a valid session token, so set it, do the request, and clear.
        if cookie is not None:
            g_session_mgr.set_current_session(cookie)
        response = f(*args, **kwargs)
        g_session_mgr.clear_current_session()
 
        return response

    return session_check

def handle_error(start_response, error_code):
    """Renders the error page."""
    global g_front_end

    content = g_front_end.error().encode('utf-8')
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(str(error_code), headers)
    g_session_mgr.clear_current_session() # Housekeeping
    return [content]

def handle_error_403(start_response):
    """Renders the error page."""
    return handle_error(start_response, '403 Forbidden')

def handle_error_404(start_response):
    """Renders the error page."""
    return handle_error(start_response, '404 Not Found')

def handle_error_500(start_response):
    """Renders the error page."""
    return handle_error(start_response, '500 Internal Server Error')

def handle_redirect_exception(url, start_response):
    """Returns the redirect response."""
    start_response('302 Found', [('Location', url)])
    return []

def handle_dynamic_page_request(env, start_response, content, mime_type='text/html; charset=utf-8'):
    """Utility function called for each page handler."""
    """Makes sure the response is encoded correctly and that the headers are set correctly."""

    # Perform the page logic and encode the response.
    content = content.encode('utf-8')

    # Build the response headers.
    headers = []
    if mime_type is not None:
        headers.append(('Content-type', mime_type))

    # Return the response headers.
    start_response('200 OK', headers)

    # Return the page contents.
    return [content]

def handle_static_file_request(start_response, dir, file_name, mime_type):
    """Utility function called for each static resource request."""

    # Sanity checks.
    if [start_response, dir, file_name, mime_type].count(None) > 0:
        return handle_error_404(start_response)
    if dir.find('..') != -1:
        return handle_error_404(start_response)
    if file_name.find('..') != -1:
        return handle_error_404(start_response)

    # Clean up the provided file name. A leading slash will screw everything up.
    if file_name[0] == '/':
        file_name = file_name[1:]

    # Calculate the local file name.
    root_dir = os.path.dirname(os.path.abspath(__file__))
    local_file_name = os.path.join(root_dir, dir, file_name)

    # Sanity check the local file.
    if not InputChecker.is_safe_path(local_file_name):
        return handle_error_403(start_response)

    # Read and return the file.
    if os.path.exists(local_file_name):
        with open(local_file_name, "rb") as in_file:
            content = in_file.read()
            headers = [('Content-type', mime_type)]
            start_response('200 OK', headers)
            return [content]

    # Something went wrong. Return an error.
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response('404 Not Found', headers)
    return []

def log_error(log_str):
    """Writes an error message to the log file."""
    logger = logging.getLogger()
    logger.error(log_str)

def css(env, start_response):
    """Returns the CSS page."""
    try:
        return handle_static_file_request(start_response, Dirs.CSS_DIR, env['PATH_INFO'], 'text/css')
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def data(env, start_response):
    """Returns the data page."""
    try:
        return handle_static_file_request(start_response, Dirs.DATA_DIR, env['PATH_INFO'], 'text/plain')
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def js(env, start_response):
    """Returns the JS page."""
    try:
        return handle_static_file_request(start_response, Dirs.JS_DIR, env['PATH_INFO'], 'text/html')
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def images(env, start_response):
    """Returns images."""
    try:
        return handle_static_file_request(start_response, Dirs.IMAGES_DIR, env['PATH_INFO'], 'text/html')
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def media(env, start_response):
    """Returns media files (icons, etc.)."""
    try:
        return handle_static_file_request(start_response, Dirs.MEDIA_DIR, env['PATH_INFO'], 'text/html')
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def photos(env, start_response):
    """Returns an activity photo."""
    try:
        parts = os.path.split(env['PATH_INFO'])
        return handle_static_file_request(start_response, Dirs.PHOTOS_DIR, os.path.join(parts[0], parts[1]), 'text/html')
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def error(env, start_response):
    """Renders the error page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.render_error())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def stats(env, start_response):
    """Renders the internal statistics page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.performance_stats())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def live(env, start_response):
    """Renders the map page for the current activity from a single device."""
    global g_front_end

    try:
        device_str = env['PATH_INFO']
        device_str = device_str[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.live_device(device_str))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def live_user(env, start_response):
    """Renders the map page for the current activity from a specified user."""
    global g_front_end

    try:
        user_str = env['PATH_INFO']
        user_str = user_str[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.live_user(user_str))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def activity(env, start_response):
    """Renders the details page for an activity."""
    global g_front_end

    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.activity(activity_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def edit_activity(env, start_response):
    """Renders the edit page for an activity."""
    global g_front_end

    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.edit_activity(activity_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def trim_activity(env, start_response):
    """Renders the trim page for an activity."""
    global g_front_end

    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.trim_activity(activity_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def merge_activity(env, start_response):
    """Renders the merge page for an activity."""
    global g_front_end

    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.merge_activity(activity_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def add_photos(env, start_response):
    """Renders the add photos page for an activity."""
    global g_front_end

    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.add_photos(activity_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def device(env, start_response):
    """Renders the map page for a single device."""
    global g_front_end

    try:
        device_str = env['PATH_INFO']
        device_str = device_str[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.device(device_str))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def my_activities(env, start_response):
    """Renders the list of the specified user's activities."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.my_activities())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def all_activities(env, start_response):
    """Renders the list of all activities the specified user is allowed to view."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.all_activities())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def record_progression(env, start_response):
    """Renders the list of records, in order of progression, for the specified user and record type."""
    global g_front_end

    try:
        params = env['PATH_INFO']
        activity_type = params[1]
        record_name = params[2]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.record_progression(activity_type, record_name))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def workouts(env, start_response):
    """Renders the workouts view."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.workouts())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def workout(env, start_response):
    """Renders the view for an individual workout."""
    global g_front_end

    try:
        workout_id = env['PATH_INFO']
        workout_id = workout_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.workout(workout_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def statistics(env, start_response):
    """Renders the statistics view."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.user_stats())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def gear(env, start_response):
    """Renders the list of all gear belonging to the logged in user."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.gear())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def service_history(env, start_response):
    """Renders the service history for a particular piece of gear."""
    global g_front_end

    try:
        gear_id = env['PATH_INFO']
        gear_id = gear_id[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.service_history(gear_id))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def friends(env, start_response):
    """Renders the list of users who are friends with the logged in user."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.friends())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def device_list(env, start_response):
    """Renders the list of a user's devices."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.device_list())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def manual_entry(env, start_response):
    """Called when the user selects an activity type, indicating they want to make a manual data entry."""
    global g_front_end

    try:
        activity_type = env['PATH_INFO']
        activity_type = activity_type[1:]
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.manual_entry(activity_type))
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def import_activity(env, start_response):
    """Renders the import page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.import_activity())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def add_pace_plan(env, start_response):
    """Renders the add pace plan page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.add_pace_plan())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def pace_plans(env, start_response):
    """Renders the pace plans page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.pace_plans())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def task_status(env, start_response):
    """Renders the import status page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.task_status())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def profile(env, start_response):
    """Renders the user's profile page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.profile())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def settings(env, start_response):
    """Renders the user's settings page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.settings())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def login(env, start_response):
    """Renders the login page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.login())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def create_login(env, start_response):
    """Renders the create login page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.create_login())
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def logout(env, start_response):
    """Ends the logged in session."""
    global g_session_mgr

    _, _, _, cookie = get_verb_path_params_and_cookie(env)
    g_session_mgr.invalidate_session_token(cookie)
    return handle_dynamic_page_request(env, start_response, g_front_end.backend.login())

def about(env, start_response):
    """Renders the about page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.about())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def status(env, start_response):
    """Renders the status page. Used as a simple way to tell if the site is up."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.status())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def ical(env, start_response):
    """Returns the ical calendar with the specified ID."""
    global g_front_end

    try:
        calendar_id = env['PATH_INFO']
        calendar_id = calendar_id[1:]
        handled, response = g_front_end.backend.ical(calendar_id)
        if handled:
            return handle_dynamic_page_request(env, start_response, response)
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def api_keys(env, start_response):
    """Renders the api key management page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.api_keys())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_auth_check
def admin(env, start_response):
    """Renders the admin page."""
    global g_front_end

    try:
        return handle_dynamic_page_request(env, start_response, g_front_end.backend.admin())
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

def api(env, start_response):
    """Endpoint for API calls."""
    global g_front_end

    try:
        # Extract the things we need from the request.
        verb, path, params, cookie = get_verb_path_params_and_cookie(env)
        g_session_mgr.set_current_session(cookie)

        # Handle the API request.
        content, response_code = g_front_end.api_internal(verb, tuple(path), params, cookie)

        # Housekeeping.
        g_session_mgr.clear_current_session()

        # Return the response headers.
        if response_code == 200:
            headers = []
            headers.append(('Content-type', 'application/json'))

            content = content.encode('utf-8')
            start_response('200 OK', headers)
            return [content]
        elif response_code == 404:
            return handle_error_404(start_response)
    except ApiException.ApiException as e:
        return handle_error(start_response, e.code)
    except:
        # Log the error and then fall through to the error page response.
        log_error(traceback.format_exc())
        log_error(sys.exc_info()[0])
    return handle_error_500(start_response)

@do_session_check
def google_maps(env, start_response):
    """Returns the Google Maps API key."""
    global g_front_end

    try:
        return handle_dynamic_page_request(start_response, g_front_end.google_maps())
    except cherrypy.HTTPRedirect as e:
        return handle_redirect_exception(e.urls[0], start_response)
    except App.RedirectException as e:
        return handle_redirect_exception(e.url, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

@do_session_check
def index(env, start_response):
    """Renders the index page."""
    return login(env, start_response)

def create_server(config, port_num):
    """Returns a cherrypy server object."""

    # Instantiate a new server object.
    server = cherrypy._cpserver.Server()

    # Configure the server object.
    server.socket_host = "0.0.0.0"
    server.socket_port = port_num
    server.thread_pool = 30
    
    # HTTPS stuff.
    if config.is_https_enabled():

        cert_file = config.get_certificate_file()
        privkey_file = config.get_private_key_file()

        if len(cert_file) > 0 and len(privkey_file) > 0:
            print("Certificate File: " + cert_file)
            print("Private Key File: " + privkey_file)

            server.ssl_module = 'pyopenssl'
            server.ssl_certificate = cert_file
            server.ssl_private_key = privkey_file
        else:
            print("No certs provided.")

    # Subscribe this server.
    server.subscribe()

    return server

def main():
    """Entry point for the cherrypy+wsgi version of the app."""
    global g_front_end
    global g_session_mgr

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

    # Load the config file.
    config = Config.Config()
    if len(args.config) > 0:
        config.load(args.config)

    # Register the signal handler.
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Create all the objects that actually implement the functionality.
        root_dir = os.path.dirname(os.path.abspath(__file__))
        g_session_mgr = SessionMgr.CustomSessionMgr(config)
        backend, cherrypy_config = AppFactory.create_cherrypy(config, root_dir, g_session_mgr)

        # Mount the application.
        cherrypy.tree.graft(css, "/css")
        cherrypy.tree.graft(data, "/data")
        cherrypy.tree.graft(js, "/js")
        cherrypy.tree.graft(images, "/images")
        cherrypy.tree.graft(media, "/media")
        cherrypy.tree.graft(photos, "/photos")
        cherrypy.tree.graft(stats, "/stats")
        cherrypy.tree.graft(error, "/error")
        cherrypy.tree.graft(live, "/live")
        cherrypy.tree.graft(live_user, "/live_user")
        cherrypy.tree.graft(activity, "/activity")
        cherrypy.tree.graft(edit_activity, "/edit_activity")
        cherrypy.tree.graft(trim_activity, "/trim_activity")
        cherrypy.tree.graft(merge_activity, "/merge_activity")
        cherrypy.tree.graft(add_photos, "/add_photos")
        cherrypy.tree.graft(device, "/device")
        cherrypy.tree.graft(my_activities, "/my_activities")
        cherrypy.tree.graft(all_activities, "/all_activities")
        cherrypy.tree.graft(record_progression, "/record_progression")
        cherrypy.tree.graft(workouts, "/workouts")
        cherrypy.tree.graft(workout, "/workout")
        cherrypy.tree.graft(statistics, "/statistics")
        cherrypy.tree.graft(gear, "/gear")
        cherrypy.tree.graft(service_history, "/service_history")
        cherrypy.tree.graft(friends, "/friends")
        cherrypy.tree.graft(device_list, "/device_list")
        cherrypy.tree.graft(manual_entry, "/manual_entry")
        cherrypy.tree.graft(import_activity, "/import_activity")
        cherrypy.tree.graft(add_pace_plan, "/add_pace_plan")
        cherrypy.tree.graft(pace_plans, "/pace_plans")
        cherrypy.tree.graft(task_status, "/task_status")
        cherrypy.tree.graft(profile, "/profile")
        cherrypy.tree.graft(settings, "/settings")
        cherrypy.tree.graft(login, "/login")
        cherrypy.tree.graft(create_login, "/create_login")
        cherrypy.tree.graft(logout, "/logout")
        cherrypy.tree.graft(about, "/about")
        cherrypy.tree.graft(status, "/status")
        cherrypy.tree.graft(ical, "/ical")
        cherrypy.tree.graft(api_keys, "/api_keys")
        cherrypy.tree.graft(admin, "/admin")
        cherrypy.tree.graft(api, "/api")
        cherrypy.tree.graft(google_maps, "/google_maps")
        cherrypy.tree.graft(index, "/")

        # Unsubscribe the default server.
        cherrypy.server.unsubscribe()

        # Create the cherrypy object.
        g_front_end = CherryPyFrontEnd.CherryPyFrontEnd(backend)
        cherrypy.config.update(cherrypy_config)
        app = cherrypy.tree.mount(g_front_end, '/')
        app.merge(cherrypy_config)

        # Instantiate a new server object.
        servers = []
        port_num = config.get_bindport()
        num_servers = config.get_num_servers()
        if num_servers <= 0:
            num_servers = 1
        for i in range(0, num_servers):
            servers.append(create_server(config, port_num + i))

        cherrypy.config.update(cherrypy_config)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except DatabaseException.DatabaseException as e:
        print(e.message)
        sys.exit(1)

if __name__ == "__main__":
    main()
