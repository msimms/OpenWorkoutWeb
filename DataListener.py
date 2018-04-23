# Copyright 2017 Michael J Simms

import argparse
import cgi
import datetime
import json
import os
import re
import signal
import socket
import sys
import time
import SocketServer
import BaseHTTPServer
import StraenDb
import StraenKeys


g_debug = False
g_data_log = False
g_root_dir = os.path.dirname(os.path.realpath(__file__))
g_not_meta_data = ["DeviceId", "ActivityId", "ActivityName", "User Name", "Latitude", "Longitude", "Altitude", "Horizontal Accuracy", "Vertical Accuracy"]
g_listener = None


def signal_handler(signal, frame):
    log_info("Exiting...")
    if g_listener is not None:
        g_listener.shutdown()
    sys.exit(0)


def log_info(str):
    global g_debug
    global g_root_dir

    log_file_name = os.path.join(g_root_dir, "DataListener.log")
    with open(log_file_name, 'a') as f:
        current_time = datetime.datetime.now()
        log_str = current_time.isoformat() + ": " + str
        f.write(log_str + "\n")
        f.close()
        if g_debug:
            print log_str


def log_data(str):
    global g_debug
    global g_root_dir

    log_file_name = os.path.join(g_root_dir, "DataListenerInput.log")
    with open(log_file_name, 'a') as f:
        current_time = datetime.datetime.now()
        log_str = current_time.isoformat() + ": " + str
        f.write(log_str + "\n")
        f.close()
        if g_debug:
            print log_str


def parse_json_str(db, json_str):
    try:
        json_obj = json.loads(json_str)
        parse_json_loc_obj(db, json_obj)
    except ValueError, e:
        log_info("ValueError in JSON data - reason " + str(e) + ". JSON str = " + str(json_str))
    except KeyError, e:
        log_info("KeyError in JSON data - reason " + str(e) + ". JSON str = " + str(json_str))
    except:
        log_info("Error parsing JSON data. JSON str = " + str(json_str))


def parse_json_loc_obj(db, json_obj):
    try:
        # Parse required identifiers.
        device_str = json_obj["DeviceId"]
        activity_id = json_obj["ActivityId"]

        # Parse optional identifiers.
        username = ""
        try:
            username = json_obj["User Name"]
        except:
            pass

        # Parse the metadata looking for the timestamp.
        date_time = time.time()
        try:
            time_str = json_obj["Time"]
            date_time = int(time_str)
        except:
            pass

        # Parse the location data.
        try:
            lat = json_obj["Latitude"]
            lon = json_obj["Longitude"]
            alt = json_obj["Altitude"]
            db.create_location(device_str, activity_id, date_time, lat, lon, alt)
        except ValueError, e:
            log_info("ValueError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except KeyError, e:
            log_info("KeyError in JSON location data - reason " + str(e) + ". JSON str = " + str(json_obj))
        except:
            log_info("Error parsing JSON location data. JSON object = " + str(json_obj))

        # Parse the rest of the data, which will be a combination of metadata and sensor data.
        for item in json_obj.iteritems():
            key = item[0]
            value = item[1]
            if not key in g_not_meta_data:
                if key in [StraenKeys.CADENCE_KEY, StraenKeys.HEART_RATE_KEY, StraenKeys.POWER_KEY]:
                    db.create_sensordata(device_str, activity_id, date_time, key, value)
                elif key in [StraenKeys.CURRENT_SPEED_KEY, StraenKeys.CURRENT_PACE_KEY]:
                    db.create_metadata(device_str, activity_id, date_time, key, value)

        # Update the user device association.
        if len(username) > 0:
            user_id, user_hash, user_realname = db.retrieve_user(username)
            db.create_device(device_str, user_id)
    except ValueError, e:
        log_info("ValueError in JSON data - reason " + str(e) + ". JSON str = " + str(json_obj))
    except KeyError, e:
        log_info("KeyError in JSON data - reason " + str(e) + ". JSON str = " + str(json_obj))
    except:
        log_info("Error parsing JSON data. JSON object = " + str(json_obj))


class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        global g_root_dir

        if re.search('/api/v1/addlocations', self.path) != None:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

            if ctype == 'multipart/form-data':
                post_vars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                db = StraenDb.MongoDatabase(g_root_dir)
                length = int(self.headers.getheader('content-length'))
                post_vars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
                locations_str = post_vars.keys()[0]
                json_obj = json.loads(locations_str)
                for location_obj in json_obj["locations"]:
                    parse_json_loc_obj(db, location_obj)
            else:
                post_vars = {}

            self.send_response(200)
            self.end_headers()

            self.wfile.write("Content-type: text/html<BR><BR>");
            self.wfile.write("<HTML>POST OK.<BR><BR>")
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_GET(self):
        self.send_response(404, 'Bad Request: resource not found')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()


class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    allow_reuse_address = True
    port = 8081

    def __init__(self, port):
        self.port = port
        BaseHTTPServer.HTTPServer.__init__(self, ("", self.port), HTTPRequestHandler)

    def shutdown(self):
        self.socket.close()
        BaseHTTPServer.HTTPServer.shutdown(self)


class UdpDataListener(object):
    running = True
    port = 5150

    def __init__(self, port):
        self.port = port
        super(UdpDataListener, self).__init__()

    def read_line(self, sock):
        while self.running:
            data, addr = sock.recvfrom(1024)
            return data
        return None

    def listen_for_rest_messages(self):
        pass

    def listen_for_udp_packets(self):
        global g_root_dir

        log_info("Starting the app listener")

        try:
            db = StraenDb.MongoDatabase(g_root_dir)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("", self.port))

            while self.running:
                line = self.read_line(sock)
                if line:
                    parse_json_str(db, line)
                    if g_data_log:
                        log_data(line)
        except:
            log_info("Unhandled exception in run().")

        log_info("App listener stopped")

    def run(self):
        self.listen_for_udp_packets()

    def shutdown(self):
        self.running = False


def Start(protocol, port):
    global g_root_dir

    log_info("Creating the database in " + g_root_dir)
    database = StraenDb.MongoDatabase(g_root_dir)
    database.create()

    if protocol == "rest":
        g_listener = ThreadedHTTPServer(port)
        g_listener.serve_forever()
    else:
        g_listener = UdpDataListener(port)
        g_listener.run()


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootdir", type=str, action="store", default=os.path.dirname(os.path.realpath(__file__)), help="Directory for database and logs", required=False)
    parser.add_argument("--protocol", type=str, action="store", default="rest", help="udp|rest", required=False)
    parser.add_argument("--port", type=int, action="store", default=8081, help="Port on which to listen", required=False)
    parser.add_argument("--debug", action="store_true", default=False, help="", required=False)
    parser.add_argument("--datalog", action="store_true", default=False, help="", required=False)

    try:
        args = parser.parse_args()
        g_root_dir = args.rootdir
        g_debug = args.debug
        g_data_log = args.datalog
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if g_debug:
        Start(args.protocol, args.port)
    else:
        import daemon

        with daemon.DaemonContext():
            Start(args.protocol, args.port)
