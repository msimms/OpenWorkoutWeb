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

import datetime
import XmlWriter

GPX_TAG_NAME = "gpx"
GPX_TAG_NAME_METADATA = "metadata"
GPX_TAG_NAME_NAME = "name"
GPX_TAG_NAME_TRACK = "trk"
GPX_TAG_NAME_TRACKSEGMENT = "trkseg"
GPX_TAG_NAME_TRACKPOINT = "trkpt"
GPX_TAG_NAME_ELEVATION = "ele"
GPX_TAG_NAME_TIME = "time"
GPX_ATTR_NAME_VERSION = "version"
GPX_ATTR_NAME_CREATOR = "creator"
GPX_ATTR_NAME_LATITUDE = "lat"
GPX_ATTR_NAME_LONGITUDE = "lon"
GPX_TAG_NAME_EXTENSIONS = "extensions"
GPX_TPX = "gpxtpx:TrackPointExtension"
GPX_TPX_HR = "gpxtpx:hr"
GPX_TPX_CADENCE = "gpxtpx:cad"
GPX_TPX_POWER = "power"

class GpxWriter(XmlWriter.XmlWriter):
    """Formats an GPX file."""

    def __init__(self):
        XmlWriter.XmlWriter.__init__(self)

    def create_gpx(self, file_name, creator):
        self.create(file_name)

        attributes = {}
        attributes[GPX_ATTR_NAME_VERSION] = "1.1"
        attributes[GPX_ATTR_NAME_CREATOR] = creator
        attributes["xsi:schemaLocation"] = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"
        attributes["xmlns"] = "http://www.topografix.com/GPX/1/1"
        attributes["xmlns:gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        attributes["xmlns:gpxx"] = "http://www.garmin.com/xmlschemas/GpxExtensions/v3"
        attributes["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        self.open_tag_with_attributes(GPX_TAG_NAME, attributes, True)

    def close(self):
        self.close_all_tags()

    def write_metadata(self, start_time):
        self.open_tag(GPX_TAG_NAME_METADATA)
        buf = datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.write_tag_and_value(GPX_TAG_NAME_TIME, buf)
        self.close_tag()

    def write_name(self, name):
        self.write_tag_and_value(GPX_TAG_NAME_NAME, name)

    def start_track(self):
        self.open_tag(GPX_TAG_NAME_TRACK)

    def end_track(self):
        if self.current_tag() is GPX_TAG_NAME_TRACK:
            self.close_tag()

    def start_track_segment(self):
        self.open_tag(GPX_TAG_NAME_TRACKSEGMENT)

    def end_track_segment(self):
        if self.current_tag() is GPX_TAG_NAME_TRACKSEGMENT:
            self.close_tag()

    def start_trackpoint(self, lat, lon, alt, time_ms):
        if self.current_tag() is not GPX_TAG_NAME_TRACKSEGMENT:
            raise Exception("GPX write error.")

        attributes = {}
        attributes[GPX_ATTR_NAME_LONGITUDE] = str(lon)
        attributes[GPX_ATTR_NAME_LATITUDE] = str(lat)
        
        time_str = self.format_time_ms(time_ms)
        self.open_tag_with_attributes(GPX_TAG_NAME_TRACKPOINT, attributes, False)
        self.write_tag_and_value(GPX_TAG_NAME_ELEVATION, str(alt))
        self.write_tag_and_value(GPX_TAG_NAME_TIME, time_str)

    def end_trackpoint(self):
        if self.current_tag() is GPX_TAG_NAME_TRACKPOINT:
            self.close_tag()

    def start_extensions(self):
        self.open_tag(GPX_TAG_NAME_EXTENSIONS)

    def end_extensions(self):
        if self.current_tag() is GPX_TAG_NAME_EXTENSIONS:
            self.close_tag()

    def start_trackpoint_extensions(self):
        self.open_tag(GPX_TPX)
    
    def end_trackpoint_extensions(self):
        if self.current_tag() is GPX_TPX:
            self.close_tag()

    def store_heart_rate_bpm(self, heart_rate_bpm):
        if self.current_tag() is not GPX_TPX:
            raise Exception("GPX write error.")
        self.write_tag_and_value(GPX_TPX_HR, heart_rate_bpm)

    def store_cadence_rpm(self, cadence_rpm):
        if self.current_tag() is not GPX_TPX:
            raise Exception("GPX write error.")
        self.write_tag_and_value(GPX_TPX_CADENCE, cadence_rpm)
    
    def store_power_in_watts(self, power_in_watts):
        if self.current_tag() is not GPX_TPX:
            raise Exception("GPX write error.")
        self.write_tag_and_value(GPX_TPX_POWER, power_in_watts)

    def format_time_ms(self, t):
        sec  = t / 1000
        ms = t % 1000

        buf1 = datetime.datetime.utcfromtimestamp(sec).strftime('%Y-%m-%d %H:%M:%S')
        buf2 = buf1 + ".%04uZ" % ms
        return buf2
