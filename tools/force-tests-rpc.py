#!/usr/bin/env python

# Basic script to queue tests for all changes in the PostgreSQL src directory
# for each hard-coded test.  The parameters for each test are also currently
# hard-coded.

import sys
import subprocess
import getpass
import json
import requests

# TODO: write a proper usage message

branch = sys.argv[1]
user = sys.argv[2]

secret = getpass.getpass('secret: ')

BBURL = "http://147.75.56.225:8010"
headers = {'Content-Type': 'application/json'}
data = {
        "jsonrpc": "2.0",
        "method": "force",
        "id": 5432,
        }

s = requests.Session()
r = s.get(f"{BBURL}/auth/login", auth=(user, secret))

if branch == "master":
    command = ['git', 'log', 'master', '--pretty=format:"%H"', '--', 'src']
else:
    command = ['git', 'log', branch, '^master', '--pretty=format:"%H"', '--',
               'src']

with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as pipe:
    for line in pipe.stdout:
        commit = line.strip().strip('"')

        # dbt2

        data['params'] = {
                "reason": "force jsonrpc",
                "revision": commit,
                "branch": branch,
                "owner": user,
                "warehouses": 1,
                "duration": 120,
                "connection_delay": 1,
                "connections_per_processor": 1,
                "terminal_limit": 1
                }

        r = s.post(f"{BBURL}/api/v2/forceschedulers/run-dbt2" ,
                   data=json.dumps(data), headers=headers)

        # dbt3

        data['params'] = {
                "reason": "force jsonrpc",
                "revision": commit,
                "branch": branch,
                "owner": user,
                "scale": 1,
                "duration": 120,
                "connection_delay": 1,
                "connections_per_processor": 1,
                "terminal_limit": 1
                }

        r = s.post(f"{BBURL}/api/v2/forceschedulers/run-dbt3" ,
                   data=json.dumps(data), headers=headers)

        # dbt5

        data['params'] = {
                "reason": "force jsonrpc",
                "revision": commit,
                "branch": branch,
                "owner": user,
                "customers": 1000,
                "duration": 120,
                "connection_delay": 1,
                "users": 1,
                }

        r = s.post(f"{BBURL}/api/v2/forceschedulers/run-dbt5" ,
                   data=json.dumps(data), headers=headers)

        # dbt7

        data['params'] = {
                "reason": "force jsonrpc",
                "revision": commit,
                "branch": branch,
                "owner": user,
                "scale": 1,
                "duration": 120,
                "connection_delay": 1,
                "connections_per_processor": 1,
                "terminal_limit": 1
                }

        r = s.post(f"{BBURL}/api/v2/forceschedulers/run-dbt7" ,
                   data=json.dumps(data), headers=headers)
