# Copyright 2018 Michael J Simms

import cherrypy
import StraenKeys


class SessionMgr(object):
    """Class for managing sessions. A user may have more than one session"""

    def __init__(self):
        super(SessionMgr, self).__init__()

    def get_logged_in_user(self):
        """Returns the username associated with the current session."""
        return cherrypy.session.get(StraenKeys.SESSION_KEY)

    def get_logged_in_user_from_cookie(self, auth_cookie):
        """Returns the username associated with the specified authentication cookie."""
        cache_items = cherrypy.session.cache.items()
        for session_id, session in cache_items:
            if session_id == auth_cookie:
                if StraenKeys.SESSION_KEY in session:
                    return session[StraenKeys.SESSION_KEY]
        return None

    def create_new_session(self, username):
        """Starts a new session."""
        cherrypy.session.load()
        cherrypy.session.regenerate()
        cherrypy.session[StraenKeys.SESSION_KEY] = cherrypy.request.login = username
        return cherrypy.session.id

    def clear_session(self):
        """Ends the current session."""
        sess = cherrypy.session
        sess[StraenKeys.SESSION_KEY] = None
