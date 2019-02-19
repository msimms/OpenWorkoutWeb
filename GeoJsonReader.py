# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Mike Simms
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
"""Reads a GeoJson file."""

import json
import sys

if sys.version_info > (3, 0):
    import urllib.request
else:
    import urllib

class GeoJsonReader(object):
    """Reads a GeoJson file."""

    def __init__(self):
        self.data = None
        super(GeoJsonReader, self).__init__()

    def read(self, url):
        """Loads the GEO JSON data from the specified URL."""
        if sys.version_info > (3, 0):
            with urllib.request.urlopen(url) as url:
                self.data = json.loads(url.read().decode())
        else:
            response = urllib.urlopen(url)
            self.data = json.loads(response.read())

    def name_to_coordinate_map(self):
        """Returns a dictionary that maps the name of the geo region to it's coordinates, as an array (or array of arrays) of lat/lon."""
        geomap = {}
        feature_list = self.data['features']
        for feature in feature_list:
            feature_name = feature['properties']['name']
            coordinate_data = feature['geometry']['coordinates']
            geomap[feature_name] = coordinate_data
        return geomap
