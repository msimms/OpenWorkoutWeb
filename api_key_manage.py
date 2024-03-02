#! /usr/bin/env python
# -*- coding: utf-8 -*-
# 
# # MIT License
# 
# Copyright (c) 2020 Michael J Simms
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

import argparse
import uuid
import sys
import AppDatabase

def create_key(username, rate):
    db = AppDatabase.MongoDatabase()
    db.connect(None)
    user_id, _, _ = db.retrieve_user(username)
    key = str(uuid.uuid4())
    return db.create_api_key(user_id, key, rate)

def list_keys(username):
    db = AppDatabase.MongoDatabase()
    db.connect(None)
    user_id, _, _ = db.retrieve_user(username)
    return db.retrieve_api_keys(user_id)

def revoke_key(key):
    db = AppDatabase.MongoDatabase()
    db.connect(None)
    user_id, _, _ = db.retrieve_user_from_api_key(key)
    return db.delete_api_key(user_id, key)

if __name__ == "__main__":

    # Parse command line options.
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, action="store", default="", help="The name of the user for whom to create an API key", required=False)
    parser.add_argument("--key", type=str, action="store", default="", help="The API key to revoke", required=False)
    parser.add_argument("--rate", type=int, action="store", default="0", help="The maximum number of requests per day", required=False)
    parser.add_argument("--create-key", action="store_true", default=False, help="Creates a key for the specified user.", required=False)
    parser.add_argument("--list-keys", action="store_true", default=False, help="Lists keys owned by the specified user.", required=False)
    parser.add_argument("--revoke-key", action="store_true", default=False, help="Revokes the specified key.", required=False)

    try:
        args = parser.parse_args()
    except IOError as e:
        parser.error(e)
        sys.exit(1)

    if args.create_key:
        if create_key(args.user, args.rate):
            print("Key created.")
        else:
            print("Failed to create key.")
    if args.list_keys:
        keys = list_keys(args.user)
        print(keys)
    if args.revoke_key:
        if revoke_key(args.key):
            print("Key revoked.")
        else:
            print("Failed to revoke key.")
