# Copyright 2017-2018 Michael J Simms
"""Main application, contains all web page handlers"""

import argparse
import cherrypy
import json
import logging
import mako
import os
import signal
import sys

import StraenApi
import StraenApp
import DataMgr
import UserMgr

from cherrypy import tools
from cherrypy.process.plugins import Daemonizer


ACCESS_LOG = 'access.log'
ERROR_LOG = 'error.log'
LOGIN_URL = '/login'

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
                    if g_app.data_mgr.is_activity_id_public(device, activity_id):
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
        print "Terminating"
        self.app.terminate()
        self.app = None

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def update_track(self, activity_id=None, num=None, *args, **kw):
        if activity_id is None:
            return ""
        if num is None:
            return ""

        try:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return self.app.update_track(activity_id)
        except:
            pass
        return ""

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def update_metadata(self, activity_id=None, *args, **kw):
        if activity_id is None:
            return ""

        try:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return self.app.update_metadata(activity_id)
        except:
            self.log_error('Unhandled exception in update_metadata')
        return ""

    @cherrypy.expose
    def error(self, error_str=None):
        """Renders the error page."""
        try:
            cherrypy.response.status = 500
            return self.app.error(error_str)
        except:
            pass
        return self.app.error("")

    @cherrypy.expose
    def live(self, device_str):
        """Renders the map page for the current activity from a single device."""
        try:
            return self.app.live(device_str)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.live.__name__)
        return self.error()

    @cherrypy.expose
    def activity(self, activity_id, *args, **kw):
        """Renders the map page for an activity."""
        try:
            return self.app.activity(activity_id)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.activity.__name__)
        return self.error()

    @cherrypy.expose
    def device(self, device_str, *args, **kw):
        """Renders the map page for a single device."""
        try:
            return self.app.device(device_str)
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.device.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def my_activities(self, *args, **kw):
        """Renders the list of the specified user's activities."""
        try:
            return self.app.my_activities()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.all_activities()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.following()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.followers()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.device_list()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.device_list.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def upload(self, ufile):
        """Processes an upload request."""
        try:
            return self.app.upload(ufile)
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + StraenWeb.upload.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def manual_entry(self, activity_type):
        """Called when the user selects an activity type, indicating they want to make a manual data entry."""
        try:
            return self.app.manual_entry(activity_type)
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.import_activity()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.settings()
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.submit_login(email, password)
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.submit_new_login(email, realname, password1, password2)
        except StraenApp.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
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
            return self.app.login()
        except StraenApp.RedirectException as e:
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
        except StraenApp.RedirectException as e:
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
                params = kw
            else:
                cl = cherrypy.request.headers['Content-Length']
                params = cherrypy.request.body.read(int(cl))
                params = json.loads(params)

            # Process the API request.
            if len(args) > 0:
                api_version = args[0]
                if api_version == '1.0':
                    api = StraenApi.StraenApi(self.app.user_mgr, self.app.data_mgr, user_id)
                    handled, response = api.handle_api_1_0_request(args[1:], params)
                    if not handled:
                        self.log_error("Failed to handle request: " + args[1:])
                        cherrypy.response.status = 400
                    else:
                        cherrypy.response.status = 200
                else:
                    self.log_error("Failed to handle request for api version " + api_version)
                    cherrypy.response.status = 400
            else:
                cherrypy.response.status = 400
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

    root_dir = os.path.dirname(os.path.abspath(__file__))
    root_url = protocol + "://" + args.host
    if args.hostport > 0:
        root_url = root_url + ":" + str(args.hostport)
    print "Root URL is " + root_url

    if not args.debug:
        Daemonizer(cherrypy.engine).subscribe()

    signal.signal(signal.SIGINT, signal_handler)
    mako.collection_size = 100
    mako.directories = "templates"

    tempfile_dir = os.path.join(root_dir, 'tempfile')
    if not os.path.exists(tempfile_dir):
        os.makedirs(tempfile_dir)

    user_mgr = UserMgr.UserMgr(root_dir)
    data_mgr = DataMgr.DataMgr(root_dir)
    backend = StraenApp.StraenApp(user_mgr, data_mgr, root_dir, root_url, args.googlemapskey)
    g_app = StraenWeb(backend)

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # The markdown library is kinda spammy.
    markdown_logger = logging.getLogger("MARKDOWN")
    markdown_logger.setLevel(logging.ERROR)

    cherrypy.tools.straenweb_auth = cherrypy.Tool('before_handler', check_auth)

    conf = {
        '/':
        {
            'tools.staticdir.root': root_dir,
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
