# Copyright 2022 Michael J Simms

import App
import ApiException
import Keys

import cherrypy
import json
import logging
import traceback
import sys

LOGIN_URL = '/login'

g_front_end = None

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

def do_auth_check(*args, **kwargs):
    global g_front_end

    # A tool that looks in config for 'auth.require'. If found and it is not None, a login
    # is required and the entry is evaluated as a list of conditions that the user must fulfill
    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions is not None:

        # Split the URL.
        requested_url = cherrypy.request.request_line.split()[1]
        requested_url_parts = requested_url.split('/')
        requested_url_parts = filter(lambda part: part != '', requested_url_parts)

        # Have to do this differently for python2 and python3.
        if sys.version_info[0] < 3:
            first_url_part = requested_url_parts[0]
        else:
            first_url_part = next(requested_url_parts)

        # If the user is trying to view an activity then make sure they have permissions
        # to view it. First check to see if it's a public activity.
        if first_url_part == "device":

            # Have to do this differently for python2 and python3.
            if sys.version_info[0] < 3:
                url_params = requested_url_parts[1].split("?")
            else:
                url_params = next(requested_url_parts)

            if url_params is not None and len(url_params) >= 2:
                activity_params = url_params[1].split("=")
                if activity_params is not None and len(activity_params) >= 2:
                    activity_id = activity_params[1]
                    if g_front_end.data_mgr.is_activity_id_public(activity_id):
                        return

        # Check conditions for the logged in user.
        username = g_front_end.backend.user_mgr.get_logged_in_user()
        if username:
            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    raise cherrypy.HTTPRedirect(LOGIN_URL)
        else:
            raise cherrypy.HTTPRedirect(LOGIN_URL)

class CherryPyFrontEnd(object):
    """Class containing the URL handlers."""

    def __init__(self, backend):
        global g_front_end
        self.backend = backend
        g_front_end = self
        super(CherryPyFrontEnd, self).__init__()

    def terminate(self):
        """Destructor"""
        print("Terminating the cherrypy front end...")
        if self.backend is not None:
            self.backend.terminate()
            self.backend = None

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

    @cherrypy.expose
    def error(self, error_str=None):
        """Renders the error page."""
        try:
            cherrypy.response.status = 500
            return self.backend.render_error(error_str)
        except:
            pass
        return self.backend.render_error("")

    @cherrypy.expose
    def error_404(self, status, message, traceback, version):
        """Renders the 404 error page."""
        try:
            return self.backend.render_page_not_found()
        except:
            pass
        return self.backend.render_error("")

    @cherrypy.expose
    @require()
    def stats(self):
        """Renders the internal statistics page."""
        try:
            return self.backend.performance_stats()
        except:
            pass
        return self.error()

    @cherrypy.expose
    def live(self, device_str):
        """Renders the map page for the current activity from a single device."""
        try:
            return self.backend.live_device(device_str)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.live.__name__)
        return self.error()

    @cherrypy.expose
    def live_user(self, user_str):
        """Renders the map page for the current activity from a specified user."""
        try:
            return self.backend.live_user(user_str)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.live_user.__name__)
        return self.error()

    @cherrypy.expose
    def activity(self, activity_id):
        """Renders the details page for an activity."""
        try:
            return self.backend.activity(activity_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.activity.__name__)
        return self.error()

    @cherrypy.expose
    def edit_activity(self, activity_id):
        """Renders the edit page for an activity."""
        try:
            return self.backend.edit_activity(activity_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.edit_activity.__name__)
        return self.error()

    @cherrypy.expose
    def add_photos(self, activity_id):
        """Renders the add photos page for an activity."""
        try:
            return self.backend.add_photos(activity_id)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.add_photos.__name__)
        return self.error()

    @cherrypy.expose
    def device(self, device_str):
        """Renders the map page for a single device."""
        try:
            return self.backend.device(device_str)
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.device.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def my_activities(self):
        """Renders the list of the specified user's activities."""
        try:
            return self.backend.my_activities()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.my_activities.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def all_activities(self):
        """Renders the list of all activities the specified user is allowed to view."""
        try:
            return self.backend.all_activities()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.all_activities.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def record_progression(self, activity_type, record_name):
        """Renders the list of records, in order of progression, for the specified user and record type."""
        try:
            return self.backend.record_progression(activity_type, record_name)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.record_progression.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def workouts(self):
        """Renders the workouts view."""
        try:
            return self.backend.workouts()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.workouts.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def workout(self, workout_id):
        """Renders the view for an individual workout."""
        try:
            return self.backend.workout(workout_id)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.workout.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def statistics(self):
        """Renders the statistics view."""
        try:
            return self.backend.user_stats()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.statistics.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def gear(self):
        """Renders the list of all gear belonging to the logged in user."""
        try:
            return self.backend.gear()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.gear.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def service_history(self, gear_id):
        """Renders the service history for a particular piece of gear."""
        try:
            return self.backend.service_history(gear_id)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.service_history.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def friends(self):
        """Renders the list of users who are friends with the logged in user."""
        try:
            return self.backend.friends()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.friends.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def device_list(self):
        """Renders the list of a user's devices."""
        try:
            return self.backend.device_list()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.device_list.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def manual_entry(self, activity_type):
        """Called when the user selects an activity type, indicating they want to make a manual data entry."""
        try:
            return self.backend.manual_entry(activity_type)
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.manual_entry.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def import_activity(self):
        """Renders the import page."""
        try:
            return self.backend.import_activity()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.import_activity.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def pace_plans(self):
        """Renders the pace plans page."""
        try:
            return self.backend.pace_plans()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.pace_plans.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def task_status(self):
        """Renders the import status page."""
        try:
            return self.backend.task_status()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.task_status.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def profile(self):
        """Renders the user's profile page."""
        try:
            return self.backend.profile()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.profile.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def settings(self):
        """Renders the user's settings page."""
        try:
            return self.backend.settings()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.settings.__name__)
        return self.error()

    @cherrypy.expose
    def login(self):
        """Renders the login page."""
        try:
            return self.backend.login()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.login.__name__)
        return self.error()

    @cherrypy.expose
    def create_login(self):
        """Renders the create login page."""
        try:
            return self.backend.create_login()
        except:
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.create_login.__name__)
        return self.error()

    @cherrypy.expose
    def logout(self):
        """Ends the logged in session."""
        try:
            return self.backend.logout()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.logout.__name__)
        return self.error()

    @cherrypy.expose
    def about(self):
        """Renders the about page."""
        try:
            return self.backend.about()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.about.__name__)
        return self.error()

    @cherrypy.expose
    def status(self):
        """Renders the status page. Used as a simple way to tell if the site is up."""
        try:
            return self.backend.status()
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.status.__name__)
        return self.error()

    @cherrypy.expose
    def ical(self, calendar_id):
        """Returns the ical calendar with the specified ID."""
        try:
            handled, response = self.backend.ical(calendar_id)
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
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.ical.__name__)
        return self.error()

    @cherrypy.expose
    @require()
    def api_keys(self):
        """Renders the api key management page."""
        try:
            return self.backend.api_keys()
        except App.RedirectException as e:
            raise cherrypy.HTTPRedirect(e.url)
        except cherrypy.HTTPRedirect as e:
            raise e
        except:
            self.log_error(traceback.format_exc())
            self.log_error(sys.exc_info()[0])
            self.log_error('Unhandled exception in ' + CherryPyFrontEnd.api_keys.__name__)
        return self.error()

    def api_internal(self, verb, path, params):
        # Return values.
        response = ""
        http_status = 200

        # Get the logged in user, or lookup the user using the API key.
        user_id = None
        if Keys.API_KEY in params:

            # Session key.
            key = params[Keys.API_KEY]

            # Which user is associated with this key?
            user_id, _, _, max_rate = self.backend.user_mgr.retrieve_user_from_api_key(key)
            if user_id is not None:

                # Make sure the key is not being abused.
                if not self.backend.data_mgr.check_api_rate(key, max_rate):
                    user_id = None
                    response = "Excessive API requests."
                    http_status = 429
                    self.log_error(response)

        else:

            # API key not provided, check the session key.
            username = self.backend.user_mgr.get_logged_in_user()
            if username is not None:
                user_id, _, _ = self.backend.user_mgr.retrieve_user(username)

        # Process the API request.
        if len(path) > 0:
            api_version = path[0]
            if api_version == '1.0':
                method = path[1:]
                handled, response = self.backend.api(user_id, verb, method[0], params)
                if not handled:
                    response = "Failed to handle request: " + str(method)
                    self.log_error(response)
                    http_status = 400
                else:
                    http_status = 200
            else:
                self.log_error("Failed to handle request for api version " + api_version)
                http_status = 400
        else:
            http_status = 400

        return response, http_status

    @cherrypy.expose
    def api(self, *args, **kw):
        """Endpoint for API calls."""

        # Return values.
        response = ""
        http_status = 200
        params = {}

        try:
            # Things we need.
            verb = cherrypy.request.method

            # The API params.
            if verb == "GET":
                params = kw
            else:
                content_len = int(cherrypy.request.headers['Content-Length'])
                if content_len > 0:
                    params = cherrypy.request.body.read(content_len)
                    params = json.loads(params)

            # Pass off to the internal handler, i.e. the method that doesn't use cherrypy objects.
            response, http_status = self.api_internal(verb, args, params)

        except ApiException.ApiException as e:
            response = e.message
            http_status = e.code
            self.log_error(str(e))
        except Exception as e:
            response = "Unhandled error."
            http_status = 500
            self.log_error(str(e))
        except:
            response = "Unspecified error."
            http_status = 500
            self.log_error("Untyped exception")

        cherrypy.response.status = http_status
        return response

    @cherrypy.expose
    def google_maps(self):
        """Returns the Google Maps API key."""
        raise cherrypy.HTTPRedirect("https://maps.googleapis.com/maps/api/js?key=" + self.backend.google_maps_key)

    @cherrypy.expose
    def index(self):
        """Renders the index page."""
        return self.login()
