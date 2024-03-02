# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2019 Michael J Simms
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
"""Given a lat/lon, searches world maps to determine the political entity containing that position."""

import inspect
import os
import sys
import GeoJsonReader

# Locate and load the statistics module (the functions we're using in are made obsolete in Python 3, but we want to work in Python 2, also)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
libmathdir = os.path.join(currentdir, 'LibMath', 'python')
sys.path.insert(0, libmathdir)
import graphics

class MapSearch(object):
    """Given a lat/lon, searches world maps to determine the political entity containing that position."""

    def __init__(self, world_data_url, us_data_url, canadian_data_url):
        self.world_data = GeoJsonReader.GeoJsonReader()
        self.world_data.read(world_data_url)
        self.world_coordinates = self.world_data.name_to_coordinate_map()

        self.us_data = GeoJsonReader.GeoJsonReader()
        self.us_data.read(us_data_url)
        self.us_coordinates = self.us_data.name_to_coordinate_map()

        self.canadian_data = GeoJsonReader.GeoJsonReader()
        self.canadian_data.read(canadian_data_url)
        self.canadian_coordinates = self.canadian_data.name_to_coordinate_map()

        self.last_country = None
        self.last_us_state = None
        self.last_canadian_province = None

        super(MapSearch, self).__init__()

    def is_in_region(self, region, lat, lon):
        """Returns True if the specified lat and lon is within the bounds of the given polygon."""
        if isinstance(region, list):
            if graphics.is_point_in_poly_array(lon, lat, region):
                return True
            for subregion in region:
                if self.is_in_region(subregion, lat, lon):
                    return True
        return False

    def is_in_country(self, country_name, lat, lon):
        """Returns True if the specified lat and lon is within the bounds of the given country."""
        coordinate_list = self.world_coordinates[country_name]
        return self.is_in_region(coordinate_list, lat, lon)

    def which_country(self, lat, lon):
        """Given a lat/lon, returns the name of the country in which it falls, or empty string if not found."""

        # Test against the last country we used, since there's a good chance it'll be in the same one.
        if self.last_country:
            if self.is_in_country(self.last_country, lat, lon):
                return self.last_country

        # Loop through each country until we find a match.
        for country_name in self.world_coordinates.keys():
            if self.is_in_country(country_name, lat, lon):
                self.last_country = country_name
                return country_name
        return None

    def is_in_us_state(self, state_name, lat, lon):
        """Returns True if the specified lat and lon is within the bounds of the given US state."""
        coordinate_list = self.us_coordinates[state_name]
        return self.is_in_region(coordinate_list, lat, lon)

    def which_us_state(self, lat, lon):
        """Given a lat/lon, returns the name of the US state in which it falls, or empty string if not found."""

        # Test against the last state we used, since there's a good chance it'll be in the same one.
        if self.last_us_state:
            if self.is_in_us_state(self.last_us_state, lat, lon):
                return self.last_us_state

        # Loop through each state until we find a match.
        for state_name in self.us_coordinates.keys():
            if self.is_in_us_state(state_name, lat, lon):
                self.last_us_state = state_name
                return state_name
        return None

    def is_in_canadian_province(self, province_name, lat, lon):
        """Returns True if the specified lat and lon is within the bounds of the given US state."""
        coordinate_list = self.canadian_coordinates[province_name]
        return self.is_in_region(coordinate_list, lat, lon)

    def which_canadian_province(self, lat, lon):
        """Given a lat/lon, returns the name of the Canadian province in which it falls, or empty string if not found."""

        # Test against the last province we used, since there's a good chance it'll be in the same one.
        if self.last_canadian_province:
            if self.is_in_canadian_province(self.last_canadian_province, lat, lon):
                return self.last_canadian_province

        # Loop through each province until we find a match.
        for province_name in self.canadian_coordinates.keys():
            if self.is_in_canadian_province(province_name, lat, lon):
                self.last_canadian_province = province_name
                return province_name
        return None

    def search_map(self, lat, lon):
        """Given a lat/lon, returns an array containing the place description, from most significant to least significant, i.e. ['United States', 'Florida']"""
        description = []
        country = self.which_country(lat, lon)
        if country:
            description.append(country)
            if country == 'United States':
                state = self.which_us_state(lat, lon)
                if state:
                    description.append(state)
            elif country == 'Canada':
                province = self.which_canadian_province(lat, lon)
                if province:
                    description.append(province)

        return description
