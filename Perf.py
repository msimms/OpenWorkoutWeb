# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2017 Mike Simms
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
"""Performance monitoring tools."""

import timeit
import threading

g_stats_lock = threading.Lock()
g_stats_count = {}
g_stats_time = {}

def statistics(function):
    """Function decorator for usage and timing statistics."""

    def wrapper(*args, **kwargs):
        global g_stats_lock
        global g_stats_count
        global g_stats_time

        start = timeit.default_timer()
        result = function(*args, **kwargs)
        end = timeit.default_timer()
        execution_time = end - start

        g_stats_lock.acquire()
        try:
            g_stats_count[function.__name__] = g_stats_count[function.__name__] + 1
            g_stats_time[function.__name__] = g_stats_time[function.__name__] + execution_time
        except:
            g_stats_count[function.__name__] = 1
            g_stats_time[function.__name__] = execution_time
        finally:
            g_stats_lock.release()

        return result

    return wrapper
