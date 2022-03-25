# Copyright 2022 Michael J Simms

import argparse
import cherrypy
import logging
import os
import signal
import sys

import AppFactory
import CherryPyFrontEnd
import Config
import SessionMgr

if sys.version_info[0] < 3:
    from urllib import parse_qs
else:
    from urllib.parse import parse_qs

CSS_DIR = 'css'
DATA_DIR = 'data'
JS_DIR = 'js'
IMAGES_DIR = 'images'
MEDIA_DIR = 'media'
PHOTOS_DIR = 'photos'

g_front_end = None

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

def respond_to_redirect_exception(e, start_response):
    start_response('302 Found', [('Location', e.urls[0])])
    return []

def handle_error_404(start_response):
    """Renders the error page."""
    content = g_front_end.error().encode('utf-8')
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response('500 Internal Server Error', headers)
    return [content]

def handle_error_500(start_response):
    """Renders the error page."""
    content = g_front_end.error().encode('utf-8')
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response('500 Internal Server Error', headers)
    return [content]

def handle_dynamic_page_request(start_response, content, mime_type='text/html; charset=utf-8'):
    content = content.encode('utf-8')
    headers = [('Content-type', mime_type)]
    start_response('200 OK', headers)
    return [content]

def handle_static_file_request(start_response, dir, file_name, mime_type):
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
        return handle_static_file_request(start_response, CSS_DIR, env['PATH_INFO'], 'text/css')
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def data(env, start_response):
    """Returns the data page."""
    try:
        return handle_static_file_request(start_response, DATA_DIR, env['PATH_INFO'], 'text/plain')
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def js(env, start_response):
    """Returns the JS page."""
    try:
        return handle_static_file_request(start_response, JS_DIR, env['PATH_INFO'], 'text/html')
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def images(env, start_response):
    """Returns images."""
    try:
        return handle_static_file_request(start_response, IMAGES_DIR, env['PATH_INFO'], 'text/html')
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def media(env, start_response):
    """Returns media files (icons, etc.)."""
    try:
        return handle_static_file_request(start_response, MEDIA_DIR, env['PATH_INFO'], 'text/html')
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def photos(env, start_response):
    """Returns an activity photo."""
    try:
        return handle_static_file_request(start_response, PHOTOS_DIR, os.path.join(env['user_id'], env['PATH_INFO']), 'text/html')
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def error(env, start_response):
    """Renders the error page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.error())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def stats(env, start_response):
    """Renders the internal statistics page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.stats())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def live(env, start_response):
    """Renders the map page for the current activity from a single device."""
    try:
        device_str = env['PATH_INFO']
        device_str = device_str[1:]
        return handle_dynamic_page_request(start_response, g_front_end.livedevice_str())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def live_user(env, start_response):
    """Renders the map page for the current activity from a specified user."""
    try:
        user_str = env['PATH_INFO']
        user_str = user_str[1:]
        return handle_dynamic_page_request(start_response, g_front_end.live_user(user_str))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def activity(env, start_response):
    """Renders the details page for an activity."""
    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(start_response, g_front_end.activity(activity_id))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def edit_activity(env, start_response):
    """Renders the edit page for an activity."""
    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(start_response, g_front_end.edit_activity(activity_id))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def add_photos(env, start_response):
    """Renders the add photos page for an activity."""
    try:
        activity_id = env['PATH_INFO']
        activity_id = activity_id[1:]
        return handle_dynamic_page_request(start_response, g_front_end.add_photos(activity_id))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def device(env, start_response):
    """Renders the map page for a single device."""
    try:
        device_str = env['PATH_INFO']
        device_str = device_str[1:]
        return handle_dynamic_page_request(start_response, g_front_end.device(device_str))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def my_activities(env, start_response):
    """Renders the list of the specified user's activities."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.my_activities())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def all_activities(env, start_response):
    """Renders the list of all activities the specified user is allowed to view."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.all_activities())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def record_progression(env, start_response):
    """Renders the list of records, in order of progression, for the specified user and record type."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.record_progression())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def workouts(env, start_response):
    """Renders the workouts view."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.workouts())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def workout(env, start_response):
    """Renders the view for an individual workout."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.workout())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def statistics(env, start_response):
    """Renders the statistics view."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.statistics())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def gear(env, start_response):
    """Renders the list of all gear belonging to the logged in user."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.gear())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def service_history(env, start_response):
    """Renders the service history for a particular piece of gear."""
    try:
        gear_id = env['PATH_INFO']
        gear_id = gear_id[1:]
        return handle_dynamic_page_request(start_response, g_front_end.service_history(gear_id))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def friends(env, start_response):
    """Renders the list of users who are friends with the logged in user."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.friends())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def device_list(env, start_response):
    """Renders the list of a user's devices."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.device_list())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def manual_entry(env, start_response):
    """Called when the user selects an activity type, indicating they want to make a manual data entry."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.manual_entry())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def import_activity(env, start_response):
    """Renders the import page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.import_activity())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def pace_plans(env, start_response):
    """Renders the pace plans page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.pace_plans())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def task_status(env, start_response):
    """Renders the import status page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.task_status())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def profile(env, start_response):
    """Renders the user's profile page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.profile())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def settings(env, start_response):
    """Renders the user's settings page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.settings())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def login(env, start_response):
    """Renders the login page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.login())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def create_login(env, start_response):
    """Renders the create login page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.create_login())
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def logout(env, start_response):
    """Ends the logged in session."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return handle_error_500(start_response)

def about(env, start_response):
    """Renders the about page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.about())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def status(env, start_response):
    """Renders the status page. Used as a simple way to tell if the site is up."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.status())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def ical(env, start_response):
    """Returns the ical calendar with the specified ID."""
    try:
        calendar_id = env['PATH_INFO']
        calendar_id = calendar_id[1:]
        return handle_dynamic_page_request(start_response, g_front_end.ical(calendar_id))
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def api_keys(env, start_response):
    """Renders the api key management page."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.api_keys())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def api(env, start_response):
    """Endpoint for API calls."""
    try:
        verb = env['REQUEST_METHOD']
        path = env['REQUEST_URI'].split('/')[2:]
        method = path[1].split('?')
        path[1] = method[0]
        params1 = parse_qs(method[1])
        params2 = {}
        for k in params1:
            params2[k] = (params1[k])[0]
        content, response_code = g_front_end.api_internal(verb, tuple(path), params2)
        return handle_dynamic_page_request(start_response, content, mime_type='application/json')
    except:
        pass
    return handle_error_500(start_response)

def google_maps(env, start_response):
    """Returns the Google Maps API key."""
    try:
        return handle_dynamic_page_request(start_response, g_front_end.google_maps())
    except cherrypy.HTTPRedirect as e:
        return respond_to_redirect_exception(e, start_response)
    except:
        pass # Fall through to the error handler
    return handle_error_500(start_response)

def index(env, start_response):
    """Renders the index page."""
    return login(env, start_response)

def main():
    """Entry point for the cherrypy+wsgi version of the app."""
    global g_front_end

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

    # Create all the objects that actually implement the functionality.
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend, cherrypy_config = AppFactory.create_cherrypy(config, root_dir, SessionMgr.CustomSessionMgr())

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
    server = cherrypy._cpserver.Server()

    # Configure the server object.
    server.socket_host = "0.0.0.0"
    server.socket_port = 8080
    server.thread_pool = 30
    
    # HTTPS stuff.
    if config.is_https_enabled():
        cert_file = config.get_certificate_file()
        privkey_file = config.get_private_key_file()

        print("Running HTTPS....")
        print("Certificate File: " + cert_file)
        print("Private Key File: " + privkey_file)

        server.ssl_module = 'pyopenssl'
        server.ssl_certificate = cert_file
        server.ssl_private_key = privkey_file
        # server.ssl_certificate_chain = 'ssl/bundle.crt'

    # Subscribe this server.
    server.subscribe()

    # Example for a 2nd server (same steps as above):
    # Remember to use a different port

    # server2             = cherrypy._cpserver.Server()

    # server2.socket_host = "0.0.0.0"
    # server2.socket_port = 8081
    # server2.thread_pool = 30
    # server2.subscribe()

    # Start the server engine (Option 1 *and* 2)

    cherrypy.config.update(cherrypy_config)
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == "__main__":
    main()
