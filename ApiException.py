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
"""Exceptions thrown by a REST API."""

class ApiException(Exception):
    """Exception thrown by a REST API."""

    def __init__(self, *args):
        Exception.__init__(self, args)

    def __init__(self, code, message):
        self.code = code
        self.message = message
        Exception.__init__(self, code, message)

class ApiMalformedRequestException(ApiException):
    """Exception thrown by a REST API when an API request is missing required parameters."""

    def __init__(self, message):
        ApiException.__init__(self, 400, message)

class ApiAuthenticationException(ApiException):
    """Exception thrown by a REST API when user authentication fails."""

    def __init__(self, message):
        ApiException.__init__(self, 401, message)

class ApiNotLoggedInException(ApiException):
    """Exception thrown by a REST API when the user is not logged in."""

    def __init__(self):
        ApiException.__init__(self, 403, "Not logged in")
