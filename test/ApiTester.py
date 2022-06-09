#! /usr/bin/env python
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
"""Unit tests"""

import argparse
import json
import logging
import requests
import sys
import time
from urllib.parse import urljoin

ERROR_LOG = 'error.log'

def create_api_url(site_url):
    """Utility function for creating the API URL from the website's URL."""
    return urljoin(site_url, "/api/1.0/")

def print_test_title(title):
    """Utility function for print a string followed by a line of equal lenth."""
    print(title)
    print('-' * len(title))

def send_get_request(url, payload, cookies):
    """Utility function for sending an HTTP GET and returning the status code and response text."""
    s = requests.Session()
    response = s.get(url, params=payload, headers={'X-Requested-With':'XMLHttpRequest'}, cookies=cookies)

    print(f"URL: {url}")
    print(f"Response code: {response.status_code}")
    print(f"Response text: {response.text}")
    return response.status_code, response.text

def send_post_request(url, payload, cookies):
    """Utility function for sending an HTTP POST and returning the status code and response text."""
    s = requests.Session()
    response = s.post(url, data=json.dumps(payload), headers={'X-Requested-With':'XMLHttpRequest'}, cookies=cookies)

    print(f"URL: {url}")
    print(f"Response code: {response.status_code}")
    print(f"Response text: {response.text}")
    return response.status_code, response.text, s.cookies

def create_login(api_url, username, password, realname):
    """Creates a new login and session."""
    url = api_url + "create_login"
    payload = {'username': username, 'password1': password, 'password2': password, 'realname': realname}
    return send_post_request(url, payload, None)

def login(api_url, username, password):
    """Starts a new session."""
    url = api_url + "login"
    payload = {'username': username, 'password': password}
    return send_post_request(url, payload, None)

def login_status(api_url, cookies):
    """Validates a session."""
    url = api_url + "login_status"
    return send_get_request(url, {}, cookies)

def generate_api_key(api_url, cookies):
    """Generates a new API key."""
    url = api_url + "generate_api_key"
    return send_post_request(url, {}, cookies)

def delete_api_key(api_url, api_key, cookies):
    """Deletes an API key."""
    url = api_url + "delete_api_key"
    payload = {'key': api_key}
    return send_post_request(url, payload, cookies)

def request_workout_intensity_total(api_url, cookies, start_time, end_time):
    """Tests get_training_intensity_for_timeframe()."""
    url = api_url + "get_training_intensity_for_timeframe"
    payload = {'start_time': start_time, 'end_time': end_time}
    return send_get_request(url, payload, cookies)

def logout(root_url, cookies):
    """Ends the existing session."""
    url = root_url + "logout"
    return send_post_request(url, {}, cookies)

def run_login_tests(api_url, username, password, realname):
    """Logs in, or creates the user if the user does not exist."""

    # Login.
    print_test_title("Login")
    code, response_str, cookies = login(api_url, username, password)
    if code == 200:
        print("Test passed!\n")
    elif code == 401:
        print_test_title("Create Login")
        code, response_str, cookies = create_login(api_url, username, password, realname)
        if code != 200:
            raise Exception("Failed to create login.")
    else:
        raise Exception("Failed to login.")

    # Where's the session key?
    response_json = json.loads(response_str)
    cookies = {}
    cookies['session_cookie'] = response_json['cookie']

    # Login status.
    print_test_title("Login Status")
    code, _ = login_status(api_url, cookies)
    if code != 200:
        raise Exception("Login status check failed.")
    print("Test passed!\n")

    return cookies

def run_workout_analysis_tests(api_url, cookies):
    """Runs unit tests relating to workout analysis."""
    print_test_title("Request a sum of workout intensities")
    one_week = 86400 * 7
    now = int(time.time())
    start_time = now - one_week
    end_time = now
    code, _ = request_workout_intensity_total(api_url, cookies, start_time, end_time)
    if code != 200:
        raise Exception("Failed to logout.")
    print("Test passed!\n")

def run_logout_test(api_url, cookies):
    """Logs out the test user."""
    print_test_title("Logout")
    code, _, _ = logout(api_url, cookies)
    if code != 200:
        raise Exception("Failed to logout.")
    print("Test passed!\n")

def run_unit_tests(url, username, password, realname):
    """Entry point for the unit tests."""

    # Append the API path.
    print_test_title("Root URL")
    print(url + "\n")
    api_url = create_api_url(url)
    print_test_title("Root API URL")
    print(api_url + "\n")

    # Login
    cookies = run_login_tests(api_url, username, password, realname)

    # Generate an API key.
    print_test_title("Generate an API Key")
    code, api_key, _ = generate_api_key(api_url, cookies)
    if code != 200:
        raise Exception("Failed to generate an API key.")
    print("Test passed! API key is {0}\n".format(api_key))

    # Delete the API key.
    print_test_title("Delete the API Key")
    code, _, _ = delete_api_key(api_url, api_key, cookies)
    if code != 200:
        raise Exception("Failed to delete the API key.")
    print("Test passed! API key {0} was deleted\n".format(api_key))

    # Workout analysis.
    run_workout_analysis_tests(api_url, cookies)

    # Logout.
    run_logout_test(api_url, cookies)

def main():
    # Setup the logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://127.0.0.1", help="The root address of the website", required=False)
    parser.add_argument("--username", default="foo@example.com", help="The username to use for the test", required=False)
    parser.add_argument("--password", default="foobar123", help="The password to use for the test", required=False)
    parser.add_argument("--realname", default="Mr Foo", help="The user's real name", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    # Do the tests.
    try:
        run_unit_tests(args.url, args.username, args.password, args.realname)
    except Exception as e:
        print("Test aborted!\n")
        print(e)

if __name__ == "__main__":
    main()
