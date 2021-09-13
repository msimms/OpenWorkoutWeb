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

import IcsWriter
import Keys

class IcalServer(object):
    """Handles ical calendar requests."""

    def __init__(self, user_mgr, data_mgr, root_url):
        self.user_mgr = user_mgr
        self.data_mgr = data_mgr
        self.root_url = root_url
        super(IcalServer, self).__init__()

    def handle_request(self, calendar_id):
        calendar_name = "Planned Workouts"

        workouts = self.data_mgr.retrieve_workouts_by_calendar_id(calendar_id)
        if workouts is None:
            return False, ""
        ics_writer = IcsWriter.IcsWriter()

        response  = "BEGIN:VCALENDAR\n"
        response += "NAME:" + calendar_name + "\r\n"
        response += "X-WR-CALNAME:" + calendar_name + "\r\n"
        response += "VERSION:2.0\r\n" # iCal format version 2.0
        response += "CALSCALE:GREGORIAN\r\n"
        response += "METHOD:PUBLISH\r\n"

        for workout in workouts:
            unit_system = self.user_mgr.retrieve_user_setting(workout.user_id, Keys.USER_PREFERRED_UNITS_KEY)
            start_time = workout.scheduled_time
            if start_time is not None:
                summary  = workout.export_to_text(None).replace("\n", "\\n")
                summary += "\\n"
                summary += self.root_url + "/workout/" + str(workout.workout_id)
                response += ics_writer.create_event(workout.workout_id, start_time, start_time, workout.type, summary)

        response += "END:VCALENDAR\r\n"
        return True, response
