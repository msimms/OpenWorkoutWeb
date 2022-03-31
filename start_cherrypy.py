# Copyright 2017-2018 Michael J Simms
"""Main application - if using cherrypy, contains all web page handlers"""

import argparse
import cherrypy
import os
import signal
import sys

import AppFactory
import CherryPyFrontEnd
import Config
import SessionMgr

from cherrypy import tools
from cherrypy.process import plugins
from cherrypy.process.plugins import Daemonizer

ACCESS_LOG = 'access.log'

g_front_end = None

class ReloadFeature(plugins.SimplePlugin):
    """A feature that handles site reloading."""

    def start(self):
        print("ReloadFeature start")

    def stop(self):
        print("ReloadFeature stop")
        if g_front_end is not None:
            g_front_end.terminate()

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

def main():
    """Entry point for the cherrypy version of the app."""
    global g_front_end

    # Make sure we have a compatible version of python.
    if sys.version_info[0] < 3:
        print("This application requires python 3.")
        sys.exit(1)

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

    # HTTPS stuff.
    if config.is_https_enabled():
        cert_file = config.get_certificate_file()
        privkey_file = config.get_private_key_file()

        print("Running HTTPS....")
        print("Certificate File: " + cert_file)
        print("Private Key File: " + privkey_file)

        cherrypy.server.ssl_module = 'builtin'
        cherrypy.server.ssl_certificate = cert_file
        cherrypy.server.ssl_private_key = privkey_file

    # Just leave everything in the foreground when we're debugging because it makes life easier.
    if not config.is_debug_enabled():
        Daemonizer(cherrypy.engine).subscribe()

    # Register the signal handler.
    signal.signal(signal.SIGINT, signal_handler)

    # Create all the objects that actually implement the functionality.
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend, cherrypy_config = AppFactory.create_cherrypy(config, root_dir, SessionMgr.CherryPySessionMgr())

    # Create the cherrypy object.
    g_front_end = CherryPyFrontEnd.CherryPyFrontEnd(backend)

    reload_feature = ReloadFeature(cherrypy.engine)
    reload_feature.subscribe()

    cherrypy.tools.web_auth = cherrypy.Tool('before_handler', CherryPyFrontEnd.do_auth_check)
    cherrypy.config.update({
        'server.socket_host': config.get_bindname(),
        'server.socket_port': config.get_bindport(),
        'requests.show_tracebacks': False,
        'error_page.404': g_front_end.error_404,
        'log.access_file': ACCESS_LOG})
    cherrypy.quickstart(g_front_end, config=cherrypy_config)

if __name__ == "__main__":
    main()
