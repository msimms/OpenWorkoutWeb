# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Michael J Simms
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
"""The example configuration file documents the purpose of each item."""

import configparser
import logging

class Config(object):
    """Class that abstracts the configuration file."""
    """The example configuration file documents the purpose of each item."""

    def __init__(self):
        self.config = None
        super(Config, self).__init__()

    def load(self, config_file_name):
        """Loads the configuration file."""
        self.config = configparser.RawConfigParser(allow_no_value=True)
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

    def get_log_level(self):
        level_str = self.get_str('General', 'Log Level')
        if level_str.lower == "error":
            return logging.ERROR
        if level_str.lower == "warning":
            return logging.WARNING
        if level_str.lower == "info":
            return logging.INFO
        if level_str.lower == "debug":
            return logging.DEBUG
        return logging.DEBUG

    def is_debug_enabled(self):
        return self.get_bool('General', 'Debug')

    def is_profiling_enabled(self):
        return self.get_bool('General', 'Profile')

    def is_create_login_disabled(self):
        return self.get_bool('General', 'Disable Login Creation')

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

    def get_num_servers(self):
        return self.get_int('Network', 'Num Servers')

    def get_photos_dir(self):
        return self.get_str('Photos', 'Directory')

    def get_photos_max_file_size(self):
        return self.get_int('Photos', 'Max File Size')

    def get_import_max_file_size(self):
        return self.get_int('Import', 'Max File Size')

    def get_database_url(self):
        database_url = self.get_str('Database', 'Database URL')
        if database_url is None or len(database_url) == 0:
            database_url = 'localhost:27017'
        return database_url

    def get_broker_url(self):
        return self.get_str('Celery', 'Broker URL')
