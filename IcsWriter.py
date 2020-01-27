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
"""Formats data for writing to an ICS file."""

class IcsWriter(object):
    """Formats data for writing to an ICS file."""

    def __init__(self):
        super(IcsWriter, self).__init__()

    def create_event(self, event_id, start_time, stop_time, summary, description):
        """Returns an ICS-formatted string that represents a single event within a calendar."""
        buffer  = "BEGIN:VEVENT\r\n"
        buffer += "UID:" + str(event_id) + "\r\n"
        buffer += "DTSTART:" + str(start_time) + "\r\n"
        buffer += "DTEND:" + str(stop_time) + "\r\n"
        buffer += "SUMMARY:" + summary + "\r\n"
        buffer += "DESCRIPTION:" + description + "\r\n"
        buffer += "END:VEVENT\r\n"
        return buffer
        
    def create_calendar(self, event_id, start_time, stop_time, summary, description):
        """Returns an ICS-formatted string that represents an entire calendar."""
        """Use this method when generating a .ical file with just one event."""
        buffer  = "BEGIN:VCALENDAR\r\n"
        buffer += "CALSCALE:GREGORIAN\r\n"
        buffer += "VERSION:2.0\r\n"
        buffer += self.create_event(event_id, start_time, stop_time, summary, description)
        buffer += "END:VCALENDAR\r\n"
        return buffer
