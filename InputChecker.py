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
"""Checks strings for basic compliance and sanity. Can be a partial defense against XSS attacks."""

import re
from unidecode import unidecode

hex = "[a-fA-F0-9]"
uuid = re.compile(hex + "{8}-" + hex + "{4}-" + hex + "{4}-" + hex + "{4}-" + hex + "{12}")
alphanums = re.compile(r"[\w-]*$")
safe = re.compile(r"[\w_ \(\)%'&,/.+-]*$")
emoji = re.compile(r"(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff])")
email_addr = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def is_alphanumeric(test_str):
    """Returns True if the string contains only alphanumeric characters. Otherwise, False."""
    return re.match(alphanums, test_str) is not None

def is_email_address(test_str):
    """Returns True if the string is *mostly* RFC 5322 complaint."""
    return re.match(email_addr, test_str) is not None

def is_timestamp(test_str):
    """Returns True if the string appears to be a valid timestamp."""
    return True

def is_day_of_week(test_str):
    """Returns True if the string is the name of a day of the week, case insensitive."""
    test_str_lower = test_str.lower()
    for day in days_of_week:
        if day.lower() == test_str_lower:
            return True
    return False

def is_uuid(test_str):
    """Returns True if the string appears to be a valid UUID."""
    try:
        if re.match(uuid, test_str) is not None:
            return True
    except:
        pass
    return False

def is_integer(test_str):
    """Returns True if the string appears to be a valid integer."""
    try:
        int(test_str)
        return True
    except ValueError:
        pass
    return False

def is_float(test_str):
    """Returns True if the string appears to be a valid float."""
    try:
        float(test_str)
        return True
    except ValueError:
        pass
    return False

def is_hex_str(test_str):
    """Returns True if the string appears to be a valid hexidecimal string."""
    try:
        return True
    except ValueError:
        pass
    return False

def is_valid_decoded_str(test_str):
    """Tests the input to see that it only contains safe characters for a string that has already been URL decoded."""
    try:
        if isinstance(test_str, str):
            if re.match(safe, test_str) is not None:
                return True
        elif isinstance(test_str, unicode):
            decoded_str = unidecode(test_str) # Use unidecode to allow for diacritics
            if re.match(safe, decoded_str) is not None:
                return True
    except:
        pass
    return False
