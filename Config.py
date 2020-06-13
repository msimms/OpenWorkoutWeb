# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Mike Simms
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
"""Abstracts the configuration file."""

import io
import sys

if sys.version_info[0] < 3:
    import ConfigParser as configparser
else:
    import configparser


class Config(object):
    """Class that abstracts the configuration file."""

    def __init__(self):
        self.config = None
        super(Config, self).__init__()

    def load(self, config_file_name):
        """Loads the configuration file."""
        self.config = configparser.RawConfigParser(allow_no_value=True)
        if sys.version_info[0] < 3:
            with open(config_file_name) as f:
                sample_config = f.read()
            self.config.readfp(io.BytesIO(sample_config))
        else:
            self.config.read(config_file_name)

    def get_str(self, section, setting):
        try:
            value = self.config.get(section, setting)
            return value
        except configparser.NoOptionError:
            pass
        except configparser.NoSectionError:
            pass
        except:
            pass
        return ""

    def get_bool(self, section, setting):
        value = self.get_str(section, setting)
        return value.lower() == "true"

    def get_int(self, section, setting):
        value = self.get_str(section, setting)
        if len(value) > 0:
            return int(value)
        return 0

    def is_debug_enabled(self):
        return self.get_bool('General', 'Debug')

    def is_profiling_enabled(self):
        return self.get_bool('General', 'Profile')

    def is_https_enabled(self):
        return self.get_bool('Crypto', 'HTTPS')

    def get_certificate_file(self):
        return self.get_str('Crypto', 'Certificate File')

    def get_private_key_file(self):
        return self.get_str('Crypto', 'Private Key File')

    def get_google_maps_key(self):
        return self.get_str('Maps', 'Google Maps Key')

    def get_hostname(self):
        return self.get_str('Network', 'Host')

    def get_hostport(self):
        return self.get_int('Network', 'Host Port')

    def get_bindname(self):
        return self.get_str('Network', 'Bind')

    def get_bindport(self):
        return self.get_int('Network', 'Bind Port')
