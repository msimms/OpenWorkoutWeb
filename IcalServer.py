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
"""Handles ical calendar requests."""

import DataMgr
import IcsWriter

class IcalServer(object):
    """Handles ical calendar requests."""

    def __init__(self, data_mgr):
        self.data_mgr = data_mgr
        super(IcalServer, self).__init__()

    def handle_request(self, calendar_id):
        calendar_name = "Planned Workouts"
        product_id = ""
        version = 2.0

        workouts = self.data_mgr.retrieve_workouts_by_calendar_id(calendar_id)
        if workouts is None:
            return False, ""
        ics_writer = IcsWriter.IcsWriter()

        response  = "BEGIN:VCALENDAR\n"
        response += "NAME:" + calendar_name + "\n"
        response += "X-WR-CALNAME:" + product_id + "\n"
        response += "VERSION:" + str(version) + "\n"
        response += "CALSCALE:GREGORIAN\n"
        response += "METHOD:PUBLISH\n"
        for workout in workouts:
            response += "BEGIN:VEVENT\n"
            resposne += ics_writer.create_event(workout[Keys.WORKOUT_ID_KEY], workout[Keys.WORKOUT_TIME_KEY], workout[Keys.WORKOUT_DESCRIPTION_KEY])
            response += "END:VEVENT\n"
        response += "END:VCALENDAR\n"
        return True, response
