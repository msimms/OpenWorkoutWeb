# Copyright 2018 Michael J Simms

import cherrypy
import flask
import Keys


class SessionMgr(object):
    """Class for managing sessions. A user may have more than one session"""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        pass

    def get_logged_in_user_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        pass

    def create_new_session(self, username):
        """Starts a new session."""
        pass

    def clear_session(self):
        """Ends the current session."""
        pass


class CherryPySessionMgr(SessionMgr):
    """Class for managing sessions when using the cherrypy framework. A user may have more than one session"""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        return cherrypy.session.get(Keys.SESSION_KEY)

    def get_logged_in_user_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        cache_items = cherrypy.session.cache.items()
        for session_id, session in cache_items:
            if session_id == auth_cookie:
                session_user = session[0]
                if Keys.SESSION_KEY in session_user:
                    return session_user[Keys.SESSION_KEY]
        return None

    def create_new_session(self, username):
        """Starts a new session."""
        cherrypy.session.load()
        cherrypy.session.regenerate()
        cherrypy.session[Keys.SESSION_KEY] = cherrypy.request.login = username
        return cherrypy.session.id

    def clear_session(self):
        """Ends the current session."""
        sess = cherrypy.session
        sess[Keys.SESSION_KEY] = None


class FlaskSessionMgr(SessionMgr):
    """Class for managing sessions when using the flask framework. A user may have more than one session"""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        if Keys.SESSION_KEY in flask.session:
            return flask.session[Keys.SESSION_KEY]
        return None

    def get_logged_in_user_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        pass

    def create_new_session(self, username):
        """Starts a new session."""
        flask.session[Keys.SESSION_KEY] = username

    def clear_session(self):
        """Ends the current session."""
        pass
