import argparse
import json
import logging
import os
import random
import requests
import sys
import yaml
from urllib.parse import urljoin

ERROR_LOG = 'error.log'

def create_api_url(site_url):
    """Utility function for creating the API URL from the website's URL."""
    return urljoin(site_url, "/api/1.0/")

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

def fuzz_api_endpoints(url, username, password, realname, api_endpoints, num_test_cases):
    api_url = create_api_url(url)
    for _ in range(0, num_test_cases - 1):
        endpoint_index = random.randrange(len(api_endpoints) - 1)
        endpoint_url = url + api_endpoints[endpoint_index]
        print(endpoint_url)

def fuzz_api(url, username, password, realname, num_test_cases):
    # Read and parse the RAML file.
    file_name = os.path.join(os.path.dirname(__file__), '..', 'api.raml')
    stream = open(file_name, 'r')
    api_description = yaml.load(stream, Loader=yaml.Loader)

    # Extract the API endpoints.
    api_endpoints = []
    for item in api_description:
        if item[0] == '/':
            api_endpoints.append(item)
    
    fuzz_api_endpoints(url, username, password, realname, api_endpoints, num_test_cases)

def main():
    # Setup the logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://127.0.0.1", help="The root address of the website", required=False)
    parser.add_argument("--username", default="foo@example.com", help="The username to use for the test", required=False)
    parser.add_argument("--password", default="foobar123", help="The password to use for the test", required=False)
    parser.add_argument("--realname", default="Mr Foo", help="The user's real name", required=False)
    parser.add_argument("--num-test-cases", default=100, help="The number of test cases to run", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    # Some input validation.
    if args.num_test_cases <= 0:
        print("Invalid number of test cases. Must be greater than zero.")
        sys.exit(1)

    # Do the tests.
    try:
        url = create_api_url(args.url)
        fuzz_api(url, args.username, args.password, args.realname, args.num_test_cases)
    except Exception as e:
        print("Test aborted!\n")
        print(e)

if __name__ == "__main__":
    main()
