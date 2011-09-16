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

import pgutil


insert_dictionary = "INSERT INTO {}.dictionaries (match_order, name, short_desc, info) " \
                        "VALUES (%s, %s, %s, %s);"

select_dict_id = "SELECT id FROM {}.dictionaries WHERE name = %s;"

prepare_insert_definition = "PREPARE insert_definition(VARCHAR(64), TEXT) AS " \
                                "INSERT INTO {}.definitions (dict_id, word, definition) " \
                                    "VALUES (%s, $1, $2);"

execute_insert_definition = "EXECUTE insert_definition(%s, %s);"

script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} [-f conf_file] [-m match_order] [-i info_file] name short_desc dict_file".format(script_name), file=sys.stderr)
    print("Imports a bedic dictionary into pgsql.", file=sys.stderr)

def bedic2pgsql_task(cur, schema, match_order, name, short_desc, info, defs):
    cur.execute(insert_dictionary.format(schema), (match_order, name, short_desc, info))

    cur.execute(select_dict_id.format(schema), (name, ))
    dict_id = cur.fetchone()[0]

    cur.execute(prepare_insert_definition.format(schema), (dict_id, ))

    for word, definition in defs:
        cur.execute(execute_insert_definition, (word, definition))

    print("{} definitions imported".format(len(defs)))


options, (name, short_desc, dict_file) = pgutil.get_pgsql_params("m:i:", 3, usage)

match_order = options.get("-m")
if match_order is not None:
    match_order = int(match_order)

info_file = options.get("-i")

if info_file is not None:
    with open(info_file, encoding="utf-8") as f:
        info = f.read()
else:
    info = None

with open(dict_file, "r", encoding="cp1251", newline='\n') as f:
    defs = [d.split('\n', 1) for d in f.read().split('\0')[1:-1]]

defs.sort(key=lambda d: d[1])
defs.sort(key=lambda d: d[0].lower())

pgutil.process_pgsql_task(bedic2pgsql_task, match_order, name, short_desc, info, defs)
