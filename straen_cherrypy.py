# Copyright 2017-2018 Michael J Simms
"""Main application - if using cherrypy, contains all web page handlers"""

import argparse
import cherrypy
import json
import logging
import mako
import os
import signal
import sys
import traceback

import Api
import ApiException
import App
import DataMgr
import AnalysisScheduler
import ImportScheduler
import SessionMgr
import UserMgr
import WorkoutPlanGeneratorScheduler

from cherrypy import tools
from cherrypy.process import plugins
from cherrypy.process.plugins import Daemonizer


ACCESS_LOG = 'access.log'
ERROR_LOG = 'error.log'
LOGIN_URL = '/login'


g_app = None


class ReloadFeature(plugins.SimplePlugin):
    """A feature that handles site reloading."""

    def start(self):
        print("ReloadFeature start")

    def stop(self):
        print("ReloadFeature stop")
        if g_app is not None:
            g_app.terminate()


def signal_handler(signal, frame):
    global g_app

    print("Exiting...")
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

        # Have to do this differently for python2 and 3.
        if sys.version_info[0] < 3:
            first_url_part = requested_url_parts[0]
        else:
            first_url_part = next(requested_url_parts)

        # If the user is trying to view an activity then make sure they have permissions
        # to view it. First check to see if it's a public activity.
        if first_url_part == "device":

            # Have to do this differently for python2 and 3.
            if sys.version_info[0] < 3:
                url_params = requested_url_parts[1].split("?")
            else:
                url_params = next(requested_url_parts)

            if url_params is not None and len(url_params) >= 2:
                activity_params = url_params[1].split("=")
                if activity_params is not None and len(activity_params) >= 2:
                    activity_id = activity_params[1]
                    if g_app.data_mgr.is_activity_id_public(activity_id):
                        return

        username = g_app.app.user_mgr.get_logged_in_user()
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

    def __init__(self, app):
        self.app = app
        super(StraenWeb, self).__init__()

    def terminate(self):
        """Destructor"""
        print("Terminating the cherrypy front end...")
        if self.app is not None:
            self.app.terminate()
            self.app = None

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

    @cherrypy.expose
    def stats(self):
        """Renders the internal statistics page."""
        try:
            return self.app.stats()
        except:
            pass
        return self.app.render_error("")

    @cherrypy.expose
    def error(self, error_str=None):
        """Renders the error page."""
        try:
            cherrypy.response.status = 500
            return self.app.render_error(error_str)
        except:
            pass
        return self.app.render_error("")

    @cherrypy.expose
    def live(self, device_str):
        """Renders the map page for the current activity from a single device."""
        try:
            return self.app.live_device(device_str)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.live.__name__)
        return self.error()

    @cherrypy.expose
    def live_user(self, user_str):
        """Renders the map page for the current activity from a specified user."""
        try:
            return self.app.live_user(user_str)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.live_user.__name__)
        return self.error()

    @cherrypy.expose
    def activity(self, activity_id, *args, **kw):
        """Renders the details page for an activity."""
        try:
            return self.app.activity(activity_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.activity.__name__)
        return self.error()

    @cherrypy.expose
    def edit_activity(self, activity_id, *args, **kw):
        """Renders the edit page for an activity."""
        try:
            return self.app.edit_activity(activity_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.edit_activity.__name__)
        return self.error()

    @cherrypy.expose
    def device(self, device_str, *args, **kw):
        """Renders the map page for a single device."""
        try:
            return self.app.device(device_str)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.device.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def my_activities(self, *args, **kw):
        """Renders the list of the specified user's activities."""
        try:
            return self.app.my_activities()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.my_activities.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def all_activities(self, *args, **kw):
        """Renders the list of all activities the specified user is allowed to view."""
        try:
            return self.app.all_activities()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.all_activities.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def all_records(self, activity_type, record_name):
        """Renders the list of records for the specified user and record type."""
        try:
            return self.app.all_records(activity_type, record_name)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.all_records.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def record_progression(self, activity_type, record_name):
        """Renders the list of records, in order of progression, for the specified user and record type."""
        try:
            return self.app.record_progression(activity_type, record_name)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.record_progression.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def workouts(self, *args, **kw):
        """Renders the workouts view."""
        try:
            return self.app.workouts()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.workouts.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def workout(self, workout_id, *args, **kw):
        """Renders the view for an individual workout."""
        try:
            return self.app.workout(workout_id)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.workout.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def statistics(self, *args, **kw):
        """Renders the statistics view."""
        try:
            return self.app.stats()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.statistics.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def gear(self, *args, **kw):
        """Renders the list of all gear belonging to the logged in user."""
        try:
            return self.app.gear()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.gear.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def service_history(self, gear_id, *args, **kw):
        """Renders the service history for a particular piece of gear."""
        try:
            return self.app.service_history(gear_id)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.service_history.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def friends(self, *args, **kw):
        """Renders the list of users who are friends with the logged in user."""
        try:
            return self.app.friends()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.friends.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def device_list(self, *args, **kw):
        """Renders the list of a user's devices."""
        try:
            return self.app.device_list()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.device_list.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def upload(self, ufile):
        """Processes an upload request."""
        try:
            return self.app.upload(ufile)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.upload.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def manual_entry(self, activity_type):
        """Called when the user selects an activity type, indicating they want to make a manual data entry."""
        try:
            return self.app.manual_entry(activity_type)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.manual_entry.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def import_activity(self, *args, **kw):
        """Renders the import page."""
        try:
            return self.app.import_activity()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.import_activity.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def task_status(self, *args, **kw):
        """Renders the import status page."""
        try:
            return self.app.task_status()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.task_status.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def analysis_status(self, *args, **kw):
        """Renders the analysis status page."""
        try:
            return self.app.analysis_status()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.analysis_status.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def profile(self, *args, **kw):
        """Renders the user's profile page."""
        try:
            return self.app.profile()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.profile.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def settings(self, *args, **kw):
        """Renders the user's settings page."""
        try:
            return self.app.settings()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.settings.__name__)
        return self.error()

    @cherrypy.expose
    def login(self):
        """Renders the login page."""
        try:
            return self.app.login()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            return self.error()
        return self.error()

    @cherrypy.expose
    def create_login(self):
        """Renders the create login page."""
        try:
            return self.app.create_login()
        except:
            return self.error()
        return self.error()

    @cherrypy.expose
    def logout(self):
        """Ends the logged in session."""
        try:
            return self.app.logout()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            return self.error()
        return self.error()

    @cherrypy.expose
    def about(self):
        """Renders the about page."""
        result = ""
        try:
            result = self.app.about()
        except:
            result = self.error()
        return result

    @cherrypy.expose
    def status(self):
        """Renders the status page. Used as a simple way to tell if the site is up."""
        result = ""
        try:
            result = self.app.status()
        except:
            result = self.error()
        return result

    @cherrypy.expose
    def ical(self, calendar_id):
        """Returns the ical calendar with the specified ID."""
        try:
            handled, response = self.app.ical(calendar_id)
            if not handled:
                cherrypy.response.status = 400
            return response
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + StraenWeb.ical.__name__)
        return self.error()

    @cherrypy.expose
    def api(self, *args, **kw):
        """Endpoint for API calls."""
        response = ""
        try:
            # Get the logged in user.
            user_id = None
            username = self.app.user_mgr.get_logged_in_user()
            if username is not None:
                user_id, _, _ = self.app.user_mgr.retrieve_user(username)

            # The the API params.
            if cherrypy.request.method == "GET":
                verb = "GET"
                params = kw
            else:
                verb = "POST"
                cl = int(cherrypy.request.headers['Content-Length'])
                if cl > 0:
                    params = cherrypy.request.body.read(cl)
                    params = json.loads(params)
                else:
                    params = []

            # Process the API request.
            if len(args) > 0:
                api_version = args[0]
                if api_version == '1.0':
                    method = args[1:]
                    handled, response = self.app.api(user_id, verb, method[0], params)
                    if not handled:
                        response = "Failed to handle request: " + str(method)
                        self.log_error(response)
                        cherrypy.response.status = 400
                    else:
                        cherrypy.response.status = 200
                else:
                    self.log_error("Failed to handle request for api version " + api_version)
                    cherrypy.response.status = 400
            else:
                cherrypy.response.status = 400
        except ApiException as e:
            self.log_error(e.message)
            cherrypy.response.status = e.code
        except Exception as e:
            response = str(e.args[0])
            self.log_error(response)
            cherrypy.response.status = 500
        except:
            cherrypy.response.status = 500
        return response

    @cherrypy.expose
    def index(self):
        """Renders the index page."""
        return self.login()

def main():
    """Entry point for the cherrypy version of the app."""
    global g_app

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False, help="Prevents the app from going into the background.", required=False)
    parser.add_argument("--profile", action="store_true", default=False, help="Enables application profiling.", required=False)
    parser.add_argument("--host", default="", help="Host name on which users will access this website.", required=False)
    parser.add_argument("--hostport", type=int, default=0, help="Port on which users will access this website.", required=False)
    parser.add_argument("--bind", default="127.0.0.1", help="Host name on which to bind.", required=False)
    parser.add_argument("--bindport", type=int, default=8080, help="Port on which to bind.", required=False)
    parser.add_argument("--https", action="store_true", default=False, help="Runs the app as HTTPS.", required=False)
    parser.add_argument("--cert", default="cert.pem", help="Certificate file for HTTPS.", required=False)
    parser.add_argument("--privkey", default="privkey.pem", help="Private Key file for HTTPS.", required=False)
    parser.add_argument("--googlemapskey", default="", help="API key for Google Maps. If not provided OpenStreetMap will be used.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if args.https:
        print("Running HTTPS....")
        cherrypy.server.ssl_module = 'builtin'
        cherrypy.server.ssl_certificate = args.cert
        print("Certificate File: " + args.cert)
        cherrypy.server.ssl_private_key = args.privkey
        print("Private Key File: " + args.privkey)
        protocol = "https"
    else:
        protocol = "http"

    if len(args.host) == 0:
        if args.debug:
            args.host = "127.0.0.1"
        else:
            args.host = "straen-app.com"
        print("Hostname not provided, will use " + args.host)

    root_dir = os.path.dirname(os.path.abspath(__file__))
    root_url = protocol + "://" + args.host
    if args.hostport > 0:
        root_url = root_url + ":" + str(args.hostport)
    print("Root URL is " + root_url)

    if not args.debug:
        Daemonizer(cherrypy.engine).subscribe()

    # Register the signal handler.
    signal.signal(signal.SIGINT, signal_handler)

    # Configure the template engine.
    mako.collection_size = 100
    mako.directories = "templates"

    session_mgr = SessionMgr.CherryPySessionMgr()
    user_mgr = UserMgr.UserMgr(session_mgr)
    data_mgr = DataMgr.DataMgr(root_url, AnalysisScheduler.AnalysisScheduler(), ImportScheduler.ImportScheduler(), WorkoutPlanGeneratorScheduler.WorkoutPlanGeneratorScheduler())
    backend = App.App(user_mgr, data_mgr, root_dir, root_url, args.googlemapskey, args.profile, args.debug)
    g_app = StraenWeb(backend)

    # Configure the error logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # The markdown library is kinda spammy.
    markdown_logger = logging.getLogger("MARKDOWN")
    markdown_logger.setLevel(logging.ERROR)

    # The direcory for session objects.
    session_dir = os.path.join(root_dir, 'sessions')
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)

    cherrypy.tools.straenweb_auth = cherrypy.Tool('before_handler', check_auth)

    conf = {
        '/':
        {
            'tools.staticdir.root': root_dir,
            'tools.straenweb_auth.on': True,
            'tools.sessions.on': True,
            'tools.sessions.name': 'straenweb_auth',
            'tools.sessions.storage_type': 'file',
            'tools.sessions.storage_path': session_dir,
            'tools.sessions.timeout': 129600,
            'tools.sessions.locking': 'early',
            'tools.secureheaders.on': True
        },
        '/api':
        {
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Access-Control-Allow-Origin', '*')],
        },
        '/css':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'css'
        },
        '/data':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'data'
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

    reload_feature = ReloadFeature(cherrypy.engine)
    reload_feature.subscribe()

    cherrypy.quickstart(g_app, config=conf)

if __name__ == "__main__":
    main()
