# Copyright 2018 Michael J Simms

import datetime
import XmlFileWriter

class GpxFileWriter(XmlFileWriter.XmlFileWriter):
    """Formats an GPX file."""

    def __init__(self):
        GpxFileWriter.GpxFileWriter.__init__(self)

    def create_file(self, file_name, creator):
        result = False

        if super.create_file(file_name):
            attributes = []

            attribute = {}
            attribute[GPX_ATTR_NAME_VERSION] = "1.1"
            attributes.append(attribute)

            attribute[GPX_ATTR_NAME_CREATOR] = creator
            attributes.append(attribute)

            attribute["xsi:schemaLocation"] = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"
            attributes.append(attribute)

            attribute["xmlns"] = "http://www.topografix.com/GPX/1/1"
            attributes.append(attribute)

            attribute["xmlns:gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
            attributes.append(attribute)

            attribute["xmlns:gpxx"] = "http://www.garmin.com/xmlschemas/GpxExtensions/v3"
            attributes.append(attribute)

            attribute["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
            attributes.append(attribute)

            result = self.open_tag(GPX_TAG_NAME, attributes, True)
        return result

    def close_file(self):
        return self.close_all_tags()

    def write_metadata(self, start_time):
        result = False

        if self.open_tag(GPX_TAG_NAME_METADATA):
            buf = datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%dT%H:%M:%SZ')
            self.write_tag_and_value(GPX_TAG_NAME_TIME, buf)
            self.close_tag()
        return result

    def write_name(self, name):
        return self.write_tag_and_value(GPX_TAG_NAME_NAME, name)

    def start_track(self):
        return OpenTag(GPX_TAG_NAME_TRACK)

    def end_track(self):
        if self.current_tag is GPX_TAG_NAME_TRACK:
            return self.close_tag()
        return False

    def start_track_segment(self):
        return OpenTag(GPX_TAG_NAME_TRACKSEGMENT)

    def end_track_segment(self):
        if self.current_tag is GPX_TAG_NAME_TRACKSEGMENT:
            return self.close_tag()
        return False

    def start_track_point(self, lat, lon, alt, time_ms):
        if self.current_tag is not GPX_TAG_NAME_TRACKSEGMENT:
            return False

        attributes = []

        attribute = {}
        attribute[GPX_ATTR_NAME_LONGITUDE] = str(lon)
        attributes.append(attribute)

        attribute = {}
        attribute[GPX_ATTR_NAME_LATITUDE] = str(lat)
        attributes.append(attribute)
        
        time_str = self.format_time_ms(time_ms)
        if self.open_tag(GPX_TAG_NAME_TRACKPOINT, attributes, False):
            self.write_tag_and_value(GPX_TAG_NAME_ELEVATION, str(alt))
            self.write_tag_and_value(GPX_TAG_NAME_TIME, time_str)
            return True
        return False

    def end_track_point(self):
        if self.current_tag is GPX_TAG_NAME_TRACKPOINT:
            return CloseTag()
        return False

    def start_etensions(self):
        return self.open_tag(GPX_TAG_NAME_EXTENSIONS)

    def end_extensions(self):
        if self.current_tag is GPX_TAG_NAME_EXTENSIONS:
            return self.close_tag()
        return False

    def start_track_point_extensions(self):
        return self.open_tag(GPX_TPX)
    
    def end_track_point_extensions(self):
        if self.current_tag is GPX_TPX:
            return self.close_tag()
        return False

    def store_heart_rate_bpm(self, heart_rate_bpm):
        if self.current_tag is not GPX_TPX:
            return False
        return self.write_tag_and_value(GPX_TPX_HR, heart_rate_bpm)

    def store_cadence_rpm(self, cadence_rpm):
        if self.current_tag is not GPX_TPX:
            return False
        return self.write_tag_and_value(GPX_TPX_CADENCE, cadence_rpm)
    
    def store_power_in_watts(self, power_in_watts):
        if self.current_tag is not GPX_TPX:
            return False
        return self.write_tag_and_value(GPX_TPX_POWER, power_in_watts)

    def format_time_ms(self, t):
        sec  = t / 1000
        ms = t % 1000

        buf1 = datetime.datetime.utcfromtimestamp(sec).strftime('%Y-%m-%d %H:%M:%S')
        buf2 = buf1 + ".%04uZ" % ms
        return buf2
