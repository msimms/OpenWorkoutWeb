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
"""Formats an data for writing to an ICS file."""

import uuid

class IcsWriter(object):
    """Formats an data for writing to an ICS file."""

    def __init__(self):
        super(IcsWriter, self).__init__()

    def create(self, start_time, stop_time, summary):
        """Returns an ICS-formatted string."""
        buffer  = "BEGIN:VCALENDAR\n"
        buffer += "CALSCALE:GREGORIAN\n"
        buffer += "VERSION:2.0\n"
        buffer += "BEGIN:VEVENT\n"
        buffer += "UID:" + str(uuid.uuid4()) + "\n"
        buffer += "DTSTAMP:" + "\n"
        buffer += "DTSTART:" + str(start_time) + "\n"
        buffer += "DTEND:" + str(stop_time) + "\n"
        buffer += "SUMMARY:" + summary + "\n"
        buffer += "END:VEVENT\n"
        buffer += "END:VCALENDAR\n"
        return buffer
