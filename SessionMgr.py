# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2018 Mike Simms
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
"""Manages login sessions."""

import cherrypy
import flask
import logging
import os
import sys
import time
import uuid

import Keys
import SessionException

class SessionMgr(object):
    """Class for managing sessions. A user may have more than one session"""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.error(log_str)

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        pass

    def get_logged_in_user_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        pass

    def create_new_session(self, username):
        """Starts a new session."""
        pass

    def clear_current_session(self):
        """Ends the current session."""
        pass

    def session_dir(self, root_dir):
        """Returns the directory to be used for session storage."""
        session_dir = os.path.join(root_dir, 'sessions3')
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        return session_dir

class CustomSessionMgr(SessionMgr):
    """Custom session manager, avoids the logic provided by the framework. Goal is a high performance session manager."""

    def __init__(self):
        super(SessionMgr, self).__init__()
        self.session_cache = {}
        self.load_sessions()

    def load_sessions(self):
        """Loads existing session data into the cache."""
        pass

    def flush_session_data(self):
        """Flushes session data to secondary storage."""
        pass

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        if Keys.SESSION_KEY in self.session_cache:
            session = self.session_cache[Keys.SESSION_KEY]
            return session[0]
        return None

    def get_logged_in_user_from_cookie(self, session_cookie):
        """Returns the username associated with the specified session cookie."""
        user = None
        if session_cookie in self.session_cache:
            session = self.session_cache[session_cookie]
            return session[0]
        return user

    def create_new_session(self, username):
        """Starts a new session."""
        session_cookie = str(uuid.uuid4())
        now = time.time()
        self.session_cache[Keys.SESSION_KEY] = ( username, now )
        self.session_cache[session_cookie] =  ( username, now )
        self.flush_session_data()
        return session_cookie

    def clear_current_session(self):
        """Ends the current session."""
        if Keys.SESSION_KEY in self.session_cache:
            self.session_cache.pop(Keys.SESSION_KEY)

    def session_dir(self, root_dir):
        """Returns the directory to be used for session storage."""
        session_dir = os.path.join(root_dir, 'session_cache')
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        return session_dir

class CherryPySessionMgr(SessionMgr):
    """Class for managing sessions when using the cherrypy framework. A user may have more than one session."""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        try:
            user = cherrypy.session.get(Keys.SESSION_KEY)
        except AttributeError:
            self.log_error("cherrypy.session has not been instantiated.")
            user = None
        return user

    def get_logged_in_user_from_cookie(self, session_cookie):
        """Returns the username associated with the specified session cookie."""
        try:
            user = None
            cache_items = cherrypy.session.cache.items()
            for session_id, session in cache_items:
                if session_id == session_cookie:
                    session_user = session[0]
                    if Keys.SESSION_KEY in session_user:
                        user = session_user[Keys.SESSION_KEY]
        except AttributeError:
            self.log_error("cherrypy.session has not been instantiated.")
            user = None
        return user

    def create_new_session(self, username):
        """Starts a new session."""
        cherrypy.session.load()
        cherrypy.session.regenerate()
        cherrypy.session[Keys.SESSION_KEY] = cherrypy.request.login = username
        new_id = cherrypy.session.id
        return new_id

    def clear_current_session(self):
        """Ends the current session."""
        sess = cherrypy.session
        sess[Keys.SESSION_KEY] = None

class FlaskSessionMgr(SessionMgr):
    """Class for managing sessions when using the flask framework. A user may have more than one session."""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        if Keys.SESSION_KEY in flask.session:
            return flask.session[Keys.SESSION_KEY]
        return None

    def get_logged_in_user_from_cookie(self, session_cookie):
        """Returns the username associated with the specified authentication cookie."""
        pass

    def create_new_session(self, username):
        """Starts a new session."""
        flask.session[Keys.SESSION_KEY] = username

    def clear_current_session(self):
        """Ends the current session."""
        flask.session.pop(Keys.SESSION_KEY, None)
        flask.session.clear()
        raise SessionException.SessionTerminatedException()
