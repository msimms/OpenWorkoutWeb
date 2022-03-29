# Copyright 2022 Michael J Simms

import logging
import mako

import App
import DataMgr
import AnalysisScheduler
import ImportScheduler
import SessionMgr
import UserMgr
import WorkoutPlanGeneratorScheduler

ERROR_LOG = 'error.log'
ACCESS_LOG = 'access.log'

def create_cherrypy(config, root_dir, session_mgr):
    """Factory method for creating the backend when we're using the cherrypy framework."""

    # Config file things we need.
    debug_enabled = config.is_debug_enabled()
    profiling_enabled = config.is_profiling_enabled()
    host = config.get_hostname()
    hostport = config.get_hostport()
    googlemaps_key = config.get_google_maps_key()

    # Hostname cleanup.
    if len(host) == 0:
        if debug_enabled:
            host = "127.0.0.1"
        else:
            host = "openworkout.cloud"
        print("Hostname not provided, will use " + host)

    # HTTPS stuff.
    if config.is_https_enabled():
        protocol = "https"
    else:
        protocol = "http"

    # Calculate the complete root URL.
    root_url = protocol + "://" + host
    if hostport > 0:
        root_url = root_url + ":" + str(hostport)
    print("Root URL is " + root_url)

    # Configure the template engine.
    mako.collection_size = 100
    mako.directories = "templates"

    # Create all the objects that actually implement the functionality.
    user_mgr = UserMgr.UserMgr(config=config, session_mgr=session_mgr)
    analysis_scheduler = AnalysisScheduler.AnalysisScheduler()
    import_scheduler = ImportScheduler.ImportScheduler()
    workout_plan_gen = WorkoutPlanGeneratorScheduler.WorkoutPlanGeneratorScheduler()
    data_mgr = DataMgr.DataMgr(config=config, root_url=root_url, analysis_scheduler=analysis_scheduler, import_scheduler=import_scheduler, workout_plan_gen_scheduler=workout_plan_gen)
    backend = App.App(user_mgr, data_mgr, root_dir, root_url, googlemaps_key, profiling_enabled, debug_enabled)

    # Configure the error logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # The markdown library is kinda spammy.
    markdown_logger = logging.getLogger("MARKDOWN")
    markdown_logger.setLevel(logging.ERROR)

    # The direcory for session objects.
    session_dir = session_mgr.session_dir(root_dir)

    cherrypy_config = {
        '/':
        {
            'tools.staticdir.root': root_dir,
            'tools.sessions.on': True,
            'tools.sessions.httponly': True,
            'tools.sessions.name': 'web_auth',
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
        '/photos':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'photos',
        },
        '/.well-known':
        {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.well-known',
        },
    }

    return backend, cherrypy_config

def create_flask(config, root_dir):
    """Factory method for creating the backend when we're using the flask framework."""

    # Config file things we need.
    debug_enabled = config.is_debug_enabled()
    profiling_enabled = config.is_profiling_enabled()
    host = config.get_hostname()
    hostport = config.get_hostport()
    googlemaps_key = config.get_google_maps_key()

    # Hostname cleanup.
    if len(host) == 0:
        if debug_enabled:
            host = "127.0.0.1"
        else:
            host = "openworkout.cloud"
        print("Hostname not provided, will use " + host)

    # HTTPS stuff.
    if config.is_https_enabled():
        protocol = "https"
    else:
        protocol = "http"

    # Calculate the complete root URL.
    root_url = protocol + "://" + host
    if hostport > 0:
        root_url = root_url + ":" + str(hostport)
    print("Root URL is " + root_url)

    # Configure the template engine.
    mako.collection_size = 100
    mako.directories = "templates"

    # Create all the objects that actually implement the functionality.
    session_mgr = SessionMgr.FlaskSessionMgr()
    user_mgr = UserMgr.UserMgr(config=config, session_mgr=session_mgr)
    analysis_scheduler = AnalysisScheduler.AnalysisScheduler()
    import_scheduler = ImportScheduler.ImportScheduler()
    workout_plan_gen = WorkoutPlanGeneratorScheduler.WorkoutPlanGeneratorScheduler()
    data_mgr = DataMgr.DataMgr(config, root_url, analysis_scheduler, import_scheduler, workout_plan_gen)
    backend = App.App(user_mgr, data_mgr, root_dir, root_url, googlemaps_key, profiling_enabled, debug_enabled)

    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # The markdown library is kinda spammy.
    markdown_logger = logging.getLogger("MARKDOWN")
    markdown_logger.setLevel(logging.ERROR)

    return backend
