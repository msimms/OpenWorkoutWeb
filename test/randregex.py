#! /usr/bin/env python

import argparse
import random
import re
import sys
from contextlib import redirect_stdout
import io

def correct_min_and_max(min_repeat, max_repeat):
    if min_repeat == None:
        min_repeat = 0
    if max_repeat == None:
        max_repeat = 64
    return min_repeat, max_repeat

def parse_max_repeat_line(line):
    items = line.split(' ')
    min_repeat = None
    max_repeat = None
    if items[1] != 'MINREPEAT' and items[1] != 'MAXREPEAT':
        min_repeat = int(items[1])
    if items[2] != 'MINREPEAT' and items[2] != 'MAXREPEAT':
        max_repeat = int(items[2])
    return min_repeat, max_repeat

def parse_range_line(line):
    items = line.split(' ')
    min_range = int(items[1].replace('(', '').replace(',', ''))
    max_range = int(items[2].replace(')', ''))
    return min_range, max_range

def parse_literal_line(line):
    items = line.split(' ')
    return chr(int(items[1]))

def parse_category_line(line):
    items = line.split(' ')
    return items[1]

def gen_char(min_repeat, max_repeat, low_range, high_range):
    result = ""
    min_repeat, max_repeat = correct_min_and_max(min_repeat, max_repeat)
    num_chars = random.randrange(min_repeat, max_repeat + 1)
    for _ in range(0, num_chars):
        c = random.randrange(low_range, high_range + 1)
        result += chr(c)
    return result

def gen_literal(min_repeat, max_repeat, literal):
    result = ""
    min_repeat, max_repeat = correct_min_and_max(min_repeat, max_repeat)
    num_digits = random.randrange(min_repeat, max_repeat + 1)
    for _ in range(0, num_digits):
        result += literal
    return result

def gen_digits(min_repeat, max_repeat):
    result = ""
    min_repeat, max_repeat = correct_min_and_max(min_repeat, max_repeat)
    num_digits = random.randrange(min_repeat, max_repeat + 1)
    for _ in range(0, num_digits):
        c = random.randrange(0, 10)
        result += str(c)
    return result

def gen(regex_str):
    result = ""

    # Have the python regex compiler compile it with the debug flag and then parse the output.
    # Need to redirect standard I/O to do this.
    f = io.StringIO()
    with redirect_stdout(f):
        re.compile(regex_str, re.DEBUG)
    debug_out = f.getvalue()

    # Use a state machine to parse the debug out.
    debug_lines = debug_out.split('\n')
    min_repeat = 1
    max_repeat = 1
    for debug_line in debug_lines:
        
        # Count the leading spaces.
        leading_spaces = len(debug_line) - len(debug_line.lstrip(' '))

        # We should reset the state when there's no indentation.
        if leading_spaces == 0:
            min_repeat = 1
            max_repeat = 1

        # Remove leading (and trailing) spaces.
        line = debug_line.strip(' ')

        # State machine. Reset the state machine whenever the 
        if line.startswith("MAX_REPEAT"):
            min_repeat, max_repeat = parse_max_repeat_line(line)
        if line.startswith("IN"):
            pass
        if line.startswith("RANGE"):
            low_range, high_range = parse_range_line(line)
            result += gen_char(min_repeat, max_repeat, low_range, high_range)
        if line.startswith("LITERAL"):
            literal = parse_literal_line(line)
            result += gen_literal(min_repeat, max_repeat, literal)
        if line.startswith("CATEGORY"):
            category = parse_category_line(line)
            if category == 'CATEGORY_DIGIT':
                result += gen_digits(min_repeat, max_repeat)

    return result

def main():
    # Parse the command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--regex", type=str, action="store", default="", help="The regex from which to generate a random string.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    print(gen(args.regex))

if __name__ == "__main__":
    main()
