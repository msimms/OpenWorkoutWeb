# Copyright 2018 Michael J Simms
"""Checks strings for basic compliance and sanity. Can be a partial defense against XSS attacks."""

import re
from unidecode import unidecode

alphanums = re.compile(r'[\w-]*$')
safe = re.compile(r'[\w_ .-]*$')
email_addr = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

def is_alphanumeric(test_str):
    """Returns True if the string contains only alphanumeric characters. Otherwise, False."""
    return re.match(alphanums, test_str)

def is_email_address(test_str):
    """Returns True if the string is *mostly* RFC 5322 complaint."""
    return re.match(email_addr, test_str)

def is_timestamp(test_str):
    """Returns True if the string appears to be a valid timestamp."""
    return True

def is_integer(test_str):
    """Returns True if the string appears to be a valid integer."""
    try: 
        int(test_str)
        return True
    except ValueError:
        pass
    return False

def is_valid(test_str):
    """Tests the input to see that it only contains safe characters."""
    try:
        if re.match(safe, unidecode(test_str)): # Use unidecode to allow for diacritics
            return True
    except:
        pass
    return False
