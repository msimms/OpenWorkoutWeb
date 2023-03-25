import argparse
import json
import logging
import numpy as np
import os
import random
import re
import requests
import sys
import string
import yaml
from urllib.parse import urljoin

ERROR_LOG = 'error.log'
GET_VERB = 'get'
POST_VERB = 'post'

class DataGenerator(object):
    def random_hex(self, strlen):
        choices = random.choices(['a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], k=strlen)
        return ''.join(str(x) for x in choices)

    def random_str(self, strlen):
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=strlen))

    def random_uuid(self):
        uuid_str  = self.random_hex(8)
        uuid_str += '-'
        uuid_str += self.random_hex(4)
        uuid_str += '-'
        uuid_str += self.random_hex(4)
        uuid_str += '-'
        uuid_str += self.random_hex(4)
        uuid_str += '-'
        uuid_str += self.random_hex(12)
        return uuid_str

    def random_number(self):
        return random.randrange(1000)

    def random_date_only(self):
        year = np.random.normal(2000, 10, 1)
        month = np.random.normal(6, 10, 1)
        day = np.random.normal(15, 10, 1)
        return str(year) + "-" + str(month) + "-" + str(day)

    def random_time_only(self):
        hour = np.random.normal(2000, 10, 1)
        min = np.random.normal(6, 10, 1)
        sec = np.random.normal(15, 10, 1)
        return str(hour) + ":" + str(min) + ":" + str(sec)

    def random_regex(self, pattern):
        rndstr = ''.join([random.choice(re.findall('[a-z\d]', pattern)) for _ in range(len(pattern))])
        return rndstr

    def random_bool(self):
        if random.randrange(2) == 0:
            return False
        return True

class UserType(object):
    name = ""
    pattern = ""

    def __repr__(self):
        return "UserType()"
    def __str__(self):
        return "[Name: " + self.name + ", RegEx: " + str(self.pattern) + "]"
    
    def rand(self):
        return ''.join([random.choice(re.findall('[a-z\d]', self.pattern)) for _ in range(len(self.pattern))])

class ApiCall(object):
    url = ""
    params = {}
    code = 0
    response = ""
    cookies = {}

    def __repr__(self):
        return "ApiCall()"
    def __str__(self):
        return "[URL: " + self.url + ", Response: " + str(self.code) + "]"

class ApiFuzzer(object):
    user_types = []
    api_calls = []

    def create_api_url(self, site_url):
        """Utility function for creating the API URL from the website's URL."""
        return urljoin(site_url, "/api/1.0")

    def send_get_request(self, url, payload, cookies):
        """Utility function for sending an HTTP GET and returning the status code and response text."""
        s = requests.Session()
        response = s.get(url, params=payload, headers={'X-Requested-With':'XMLHttpRequest'}, cookies=cookies)

        print(f"URL: {url}")
        print(f"Parameters: " + str(payload))
        print(f"Response code: {response.status_code}")
        print(f"Response text: {response.text}")
        return response.status_code, response.text

    def send_post_request(self, url, payload, cookies):
        """Utility function for sending an HTTP POST and returning the status code and response text."""
        s = requests.Session()
        response = s.post(url, data=json.dumps(payload), headers={'X-Requested-With':'XMLHttpRequest'}, cookies=cookies)

        print(f"URL: {url}")
        print(f"Parameters: " + str(payload))
        print(f"Response code: {response.status_code}")
        print(f"Response text: {response.text}")
        return response.status_code, response.text, s.cookies

    def fuzz_param(self, param_type):
        """Returns a fuzzed value for a parameter of the specified type."""
        if param_type is None:
            return
        if param_type.lower() == 'number':
            return DataGenerator().random_number()
        if param_type.lower() == 'boolean':
            return DataGenerator().random_bool()
        if param_type.lower() == 'string':
            return DataGenerator().random_str(DataGenerator().random_number())
        if param_type.lower() == 'integer':
            return DataGenerator().random_number()
        if param_type.lower() == 'date-only':
            return DataGenerator().random_date_only()
        if param_type.lower() == 'time-only':
            return DataGenerator().random_time_only()
        if param_type.lower() == 'datetime-only':
            raise Exception("Unimplemeted type")
        if param_type.lower() == 'datetime':
            raise Exception("Unimplemeted type")
        if param_type.lower() == 'file':
            raise Exception("Unimplemeted type")
        if param_type.lower() == 'uuid':
            return DataGenerator().random_uuid()
        return ""

    def fuzz_api_params(self, substitutions, endpoint_description):
        """Returns a dictionary of fuzzed params. The list of params is given by the endpoint description"""
        fuzzed_params = {}
        if endpoint_description is not None and 'queryParameters' in endpoint_description:
            params = endpoint_description['queryParameters']
            for param_name in params:

                # Type of the parameter. Check it up here, in case we have to modify the param name later.
                param_type = params[param_name]

                # Is the parameter optional. If so, it'll end with a ?.
                if param_name[-1] == '?':
                    if DataGenerator().random_bool():
                        continue
                    param_name = param_name[:-1]

                # Special case credentials to increase our chances of actually getting somewhere.
                param_name_lower = param_name.lower()
                if param_name_lower in substitutions:
                    fuzzed_params[param_name_lower] = substitutions[param_name_lower]
                else:
                    fuzzed_params[param_name] = self.fuzz_param(param_type)

        return fuzzed_params

    def fuzz_api_endpoint(self, endpoint_url, substitutions, endpoint_description):
        """Executes a single API test."""
        api_call = ApiCall()

        # Loop through the interesting responses.
        for prev_call in self.api_calls:
            api_call.cookies = prev_call.cookies

        # Make the API call, using the verb specified in the documentation.
        api_call.url = endpoint_url
        if GET_VERB in endpoint_description:
            api_call.params = self.fuzz_api_params(substitutions, endpoint_description[GET_VERB])
            api_call.code, api_call.text = self.send_get_request(api_call.url, api_call.params, api_call.cookies)
        if POST_VERB in endpoint_description:
            api_call.params = self.fuzz_api_params(substitutions, endpoint_description[POST_VERB])
            api_call.code, api_call.text, api_call.cookies = self.send_post_request(api_call.url, api_call.params, api_call.cookies)

        # Anything other than error code 40X is interesting.
        if int(api_call.code / 100) != 4:
            self.api_calls.append(api_call)

    def fuzz_api_endpoints(self, url, substitutions, api_endpoints, api_description, num_test_cases):
        """Executes all the API test."""

        api_url = self.create_api_url(url)
        for test_num in range(0, num_test_cases - 1):
            endpoint_index = random.randrange(len(api_endpoints) - 1)
            endpoint_name = api_endpoints[endpoint_index]
            endpoint_url = api_url + endpoint_name

            print("Test " + str(test_num + 1))
            self.fuzz_api_endpoint(endpoint_url, substitutions, api_description[endpoint_name])

    def fuzz_api(self, url, substitutions, num_test_cases):
        """Primary method for executing the API tests. Parse the RAML file and then calls fuzz_api_endpoints to run the tests."""

        # Read and parse the RAML file.
        file_name = os.path.join(os.path.dirname(__file__), '..', 'api.raml')
        stream = open(file_name, 'r')
        api_description = yaml.load(stream, Loader=yaml.Loader)

        # Extract any type information from the document.
        if 'types' in api_description:
            type_descriptions = api_description['types']
            for type_name in type_descriptions:
                user_type = UserType()
                user_type.name = type_name
                user_type.pattern = type_descriptions[type_name]['pattern']
                self.user_types.append(user_type)

        # Extract the API endpoints.
        api_endpoints = []
        for item in api_description:
            if item[0] == '/':
                api_endpoints.append(item)

        # Make N number of fuzzed API calls.
        s = "Starting tests..."
        print("=" * len(s)) 
        print(s)
        print("=" * len(s)) 
        self.fuzz_api_endpoints(url, substitutions, api_endpoints, api_description, num_test_cases)

        # Print the results.
        s = "Report:"
        print("=" * len(s)) 
        print(s)
        print("=" * len(s)) 
        for api_call in self.api_calls:
            print(api_call)

def main():
    """Entry point when run from the command line."""

    # Setup the logger.
    logging.basicConfig(filename=ERROR_LOG, filemode='w', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://127.0.0.1", help="The root address of the website", required=False)
    parser.add_argument("--substitutions", default="", help="A comma separated list of key=value pairs. Parameters with a key name will be substituted, ex: username=foo@bar.com", required=False)
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

    # Parse the substitutions list.
    substitutions = {}
    for sub in args.substitutions.split(','):
        pair = sub.split('=')
        substitutions[pair[0]] = pair[1]

    # Do the tests.
    try:
        fuzzer = ApiFuzzer()
        url = fuzzer.create_api_url(args.url)
        fuzzer.fuzz_api(url, substitutions, args.num_test_cases)
    except Exception as e:
        print("Test aborted!\n")
        print(e)

if __name__ == "__main__":
    main()
