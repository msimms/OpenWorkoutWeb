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
import requests
import sys


def print_test_title(title):
    """Utility function for print a string followed by a line of equal lenth."""
    print(title)
    print('-' * len(title))

def send_post_request(url, payload):
    """Utility function for sending an HTTP POST and returning the status code and response text."""
    print("URL: " + url)
    response = requests.post(url, json=payload)
    print("Response code: " + str(response.status_code))
    print("Response text: " + response.text)
    return response.status_code, response.text

def login(root_url, username, password):
    """Starts a new session."""
    url = root_url + "login_submit"
    payload = {'username': username, 'password': password}
    return send_post_request(url, payload)

def logout(root_url, cookie):
    """Ends the existing session."""
    url = root_url + "logout"
    payload = {'_straen_username': cookie}
    return send_post_request(url, payload)

def run_unit_tests(url, username, password):
    """Entry point for the unit tests."""

    # Append the API path.
    api_url = url + "/api/1.0/"

    # Login.
    print_test_title("Login")
    code, cookie = login(api_url, username, password)
    if code == 200:
        print("Test passed!\n")
    else:
        print("Test failed!\n")

    # Logout.
    print_test_title("Logout")
    code, result = logout(api_url, cookie)
    if code == 200:
        print("Test passed!\n")
    else:
        print("Test failed!\n")

def main():
    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://127.0.0.1", help="The root address of the website", required=False)
    parser.add_argument("--username", default="foo@example.com", help="The username to use for the test", required=False)
    parser.add_argument("--password", default="foobar123", help="The password to use for the test", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    run_unit_tests(args.url, args.username, args.password)

if __name__ == "__main__":
    main()
