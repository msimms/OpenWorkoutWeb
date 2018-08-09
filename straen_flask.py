# Copyright 2018 Michael J Simms
"""Main application, contains all web page handlers"""

import argparse
import logging
import mako
import os
import signal
import sys
from flask import Flask

import DataMgr
import UserMgr
import StraenApp


ERROR_LOG = 'error.log'

g_flask_app = Flask(__name__)
g_app = None


def signal_handler(signal, frame):
    global g_app

    print "Exiting..."
    if g_app is not None:
        g_app.terminate()
    sys.exit(0)

@g_flask_app.route('/submit_new_login')
def submit_new_login(email, realname, password1, password2, *args, **kw):
    """Creates a new login."""
    try:
        return g_app.submit_new_login(email, realname, password1, password2)
    except:
        g_app.log_error('Unhandled exception in ' + submit_new_login.__name__)
    return g_app.error()

@g_flask_app.route('/login')
def login():
    """Renders the login page."""
    try:
        return g_app.login()
    except:
        return g_app.error()
    return g_app.error()

@g_flask_app.route('/create_login')
def create_login():
    """Renders the create login page."""
    try:
        return g_app.create_login()
    except:
        return g_app.error()
    return g_app.error()

@g_flask_app.route('/logout')
def logout():
    """Ends the logged in session."""
    try:
        return g_app.logout()
    except:
        return g_app.error()
    return g_app.error()

@g_flask_app.route('/about')
def about():
    """Renders the about page."""
    result = ""
    try:
        result = g_app.about()
    except:
        result = g_app.error()
    return result

@g_flask_app.route('/')
def index():
    """Renders the index page."""
    return g_app.login()

def main():
    """Entry point for the flask version of the app."""
    global g_app
    global g_flask_app

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

    signal.signal(signal.SIGINT, signal_handler)
    mako.collection_size = 100
    mako.directories = "templates"

    tempfile_dir = os.path.join(root_dir, 'tempfile')
    if not os.path.exists(tempfile_dir):
        os.makedirs(tempfile_dir)

    user_mgr = UserMgr.UserMgr(root_dir)
    data_mgr = DataMgr.DataMgr(root_dir)
    g_app = StraenApp.StraenApp(user_mgr, data_mgr, root_dir, root_url, args.googlemapskey)

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # The markdown library is kinda spammy.
    markdown_logger = logging.getLogger("MARKDOWN")
    markdown_logger.setLevel(logging.ERROR)

    g_flask_app.run()

if __name__ == '__main__':
    main()
