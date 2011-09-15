#!/usr/bin/env python3

# Copyright (C) 2011 Victor Semionov
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  * Neither the name of the copyright holder nor the names of the contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sys
import os

import psycopg2

import wbutil
import pgutil


script_name = os.path.basename(__file__)


def usage():
    print("Usage:", file=sys.stderr)
    print("    {} [-f conf_file] add name short_desc dict_name ...".format(script_name), file=sys.stderr)
    print("    {} [-f conf_file] del name".format(script_name), file=sys.stderr)
    print("Manages virtual dictionaries in pgsql.", file=sys.stderr)

def add_vdict(name, short_desc, dict_names):
    pass

def del_vdict(name):
    pass

host, port, user, password, database, schema, args = pgutil.get_pgsql_params(None, -1, usage)

if len(args) < 2:
    usage()
    sys.exit(2)

cmd_cased, name, *cmd_args = args
cmd = cmd_cased.lower()

if cmd == "add":
    if len(cmd_args) < 2:
        usage()
        sys.exit(2)
    wbutil.validate_dict_name(name)
    short_desc, *dict_names = cmd_args
    process_func_args = name, short_desc, dict_names
    process_func = add_vdict
elif cmd == "del":
    if len(cmd_args):
        usage()
        sys.exit(2)
    process_func_args = name,
    process_func = del_vdict
else:
    usage()
    sys.exit(2)

conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)

try:
    conn.autocommit = False
    cur = conn.cursor()
    try:
        process_func(*process_func_args)
    finally:
        cur.close()
    conn.commit()
finally:
    conn.close()
