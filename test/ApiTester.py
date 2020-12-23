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
import requests
import sys


def print_test_title(title):
    """Utility function for print a string followed by a line of equal lenth."""
    print(title)
    print('-' * len(title))

def send_get_request(url, payload, cookies):
    """Utility function for sending an HTTP GET and returning the status code and response text."""
    s = requests.Session()
    if cookies:
        s.cookies = cookies
    response = s.get(url, data=json.dumps(payload), headers={'X-Requested-With':'XMLHttpRequest'})

    print("URL: " + url)
    print("Response code: " + str(response.status_code))
    print("Response text: " + response.text)
    return response.status_code, response.text

def send_post_request(url, payload, cookies):
    """Utility function for sending an HTTP POST and returning the status code and response text."""
    s = requests.Session()
    if cookies:
        s.cookies = cookies
    response = s.post(url, data=json.dumps(payload), headers={'X-Requested-With':'XMLHttpRequest'})

    print("URL: " + url)
    print("Response code: " + str(response.status_code))
    print("Response text: " + response.text)
    return response.status_code, response.text, s.cookies

def create_login(root_url, username, password, realname):
    """Creates a new login and session."""
    url = root_url + "create_login"
    payload = {'username': username, 'password1': password, 'password2': password, 'realname': realname}
    return send_post_request(url, payload, None)

def login(root_url, username, password):
    """Starts a new session."""
    url = root_url + "login"
    payload = {'username': username, 'password': password}
    return send_post_request(url, payload, None)

def login_status(root_url, cookie):
    """Validates a session."""
    url = root_url + "login_status"
    return send_get_request(url, {}, cookie)

def generate_api_key(root_url, cookie):
    """Generates a new API key."""
    url = root_url + "generate_api_key"
    return send_post_request(url, {}, cookie)

def delete_api_key(root_url, api_key, cookie):
    """Deletes an API key."""
    url = root_url + "delete_api_key"
    payload = {'key': api_key}
    return send_post_request(url, payload, cookie)

def logout(root_url, cookie):
    """Ends the existing session."""
    url = root_url + "logout"
    return send_post_request(url, {}, cookie)

def run_unit_tests(url, username, password, realname):
    """Entry point for the unit tests."""

    # Append the API path.
    api_url = url + "/api/1.0/"

    # Login.
    print_test_title("Login")
    code, _, cookies = login(api_url, username, password)
    if code == 200:
        print("Test passed!\n")
    elif code == 401:
        print_test_title("Create Login")
        code, _, cookies = create_login(api_url, username, password, realname)
        if code != 200:
            raise Exception("Failed to create login.")
    else:
        raise Exception("Failed to login.")

    # Login status.
    print_test_title("Login Status")
    code, _ = login_status(api_url, cookies)
    if code == 200:
        print("Test passed!\n")
    else:
        raise Exception("Login status check failed.")

    # Generate an API key.
    print_test_title("Generate an API Key")
    code, api_key, _ = generate_api_key(api_url, cookies)
    if code == 200:
        print("Test passed! API key is {0}\n".format(api_key))
    else:
        raise Exception("Failed to generate an API key.")

    # Delete the API key.
    print_test_title("Delete the API Key")
    code, _, _ = delete_api_key(api_url, api_key, cookies)
    if code == 200:
        print("Test passed! API key {0} was deleted\n".format(api_key))
    else:
        raise Exception("Failed to delete the API key.")

    # Logout.
    print_test_title("Logout")
    code, _, _ = logout(api_url, cookies)
    if code == 200:
        print("Test passed!\n")
    else:
        raise Exception("Failed to logout.")

def main():
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

    try:
        run_unit_tests(args.url, args.username, args.password, args.realname)
    except Exception as e:
        print("Test aborted!\n")
        print(e)

if __name__ == "__main__":
    main()
