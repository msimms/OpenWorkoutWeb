# Copyright 2022 Michael J Simms

import argparse
import cherrypy
import logging
import os
import signal
import sys
import traceback

import App
import AppFactory
import CherryPyFrontEnd
import Config

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

def log_error(log_str):
    """Writes an error message to the log file."""
    logger = logging.getLogger()
    logger.error(log_str)

def error(env, start_response):
    """Renders the error page."""
    content = g_front_end.error().encode('utf-8')
    start_response('500', [('Content-Type', 'text/html')])
    return [content]

def stats(env, start_response):
    """Renders the internal statistics page."""
    try:
        content = g_front_end.stats().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def live(env, start_response):
    """Renders the map page for the current activity from a single device."""
    try:
        content = g_front_end.live().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def live_user(env, start_response):
    """Renders the map page for the current activity from a specified user."""
    try:
        content = g_front_end.live_user().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def activity(env, start_response):
    """Renders the details page for an activity."""
    try:
        content = g_front_end.activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def edit_activity(env, start_response):
    """Renders the edit page for an activity."""
    try:
        content = g_front_end.edit_activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def add_photos(env, start_response):
    """Renders the add photos page for an activity."""
    try:
        content = g_front_end.add_photos().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def device(env, start_response):
    """Renders the map page for a single device."""
    try:
        content = g_front_end.device().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def my_activities(env, start_response):
    """Renders the list of the specified user's activities."""
    try:
        content = g_front_end.my_activities().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def all_activities(env, start_response):
    """Renders the list of all activities the specified user is allowed to view."""
    try:
        content = g_front_end.all_activities().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def record_progression(env, start_response):
    """Renders the list of records, in order of progression, for the specified user and record type."""
    try:
        content = g_front_end.record_progression().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def workouts(env, start_response):
    """Renders the workouts view."""
    try:
        content = g_front_end.workouts().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def workout(env, start_response):
    """Renders the view for an individual workout."""
    try:
        content = g_front_end.workout().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def statistics(env, start_response):
    """Renders the statistics view."""
    try:
        content = g_front_end.statistics().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def gear(env, start_response):
    """Renders the list of all gear belonging to the logged in user."""
    try:
        content = g_front_end.gear().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def service_history(env, start_response):
    """Renders the service history for a particular piece of gear."""
    try:
        content = g_front_end.service_history().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def friends(env, start_response):
    """Renders the list of users who are friends with the logged in user."""
    try:
        content = g_front_end.friends().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def device_list(env, start_response):
    """Renders the list of a user's devices."""
    try:
        content = g_front_end.device_list().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def manual_entry(env, start_response):
    """Called when the user selects an activity type, indicating they want to make a manual data entry."""
    try:
        content = g_front_end.manual_entry().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def import_activity(env, start_response):
    """Renders the import page."""
    try:
        content = g_front_end.import_activity().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def pace_plans(env, start_response):
    """Renders the pace plans page."""
    try:
        content = g_front_end.pace_plans().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def task_status(env, start_response):
    """Renders the import status page."""
    try:
        content = g_front_end.task_status().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def profile(env, start_response):
    """Renders the user's profile page."""
    try:
        content = g_front_end.profile().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def settings(env, start_response):
    """Renders the user's settings page."""
    try:
        content = g_front_end.settings().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def login(env, start_response):
    """Renders the login page."""
    try:
        content = g_front_end.login().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def create_login(env, start_response):
    """Renders the create login page."""
    try:
        content = g_front_end.create_login().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except:
        pass # Fall through to error()
    return error(env, start_response)

def logout(env, start_response):
    """Ends the logged in session."""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return error(env, start_response)

def about(env, start_response):
    """Renders the about page."""
    try:
        content = g_front_end.about().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except:
        pass # Fall through to error()
    return error(env, start_response)

def status(env, start_response):
    """Renders the status page. Used as a simple way to tell if the site is up."""
    try:
        content = g_front_end.status().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except:
        pass # Fall through to error()
    return error(env, start_response)

def ical(env, start_response):
    """Returns the ical calendar with the specified ID."""
    return error(env, start_response)

def api_keys(env, start_response):
    """Renders the api key management page."""
    try:
        content = g_front_end.api_keys().encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [content]
    except App.RedirectException as e:
        start_response('302 Found', [('Location', e.url)])
        return []
    except:
        pass # Fall through to error()
    return error(env, start_response)

def api(env, start_response):
    """Endpoint for API calls."""
    return error(env, start_response)

def google_maps(env, start_response):
    """Returns the Google Maps API key."""
    global g_front_end
    start_response('302 Found', [('Location', 'https://maps.googleapis.com/maps/api/js?key=' + g_front_end.google_maps_key)])
    return []

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
    backend, cherrypy_config = AppFactory.create_cherrypy(config, root_dir)

    # Mount the application.
    cherrypy.tree.graft(log_error, "/log_error")
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
