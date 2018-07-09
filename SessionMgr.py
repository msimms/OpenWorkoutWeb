# Copyright 2018 Michael J Simms

import cherrypy


SESSION_KEY = '_straen_username'

class SessionMgr(object):
    """Class for managing sessions. A user may have more than one session"""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        return cherrypy.session.get(SESSION_KEY)

    def create_new_session(self, username):
        """Starts a new session."""
        cherrypy.session.regenerate()
        cherrypy.session[SESSION_KEY] = cherrypy.request.login = username

    def clear_session(self):
        """Ends the current session."""
        sess = cherrypy.session
        sess[SESSION_KEY] = None
