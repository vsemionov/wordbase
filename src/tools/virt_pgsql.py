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
#  * Neither the virt_name of the copyright holder nor the names of the contributors
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


insert_virtual_dictionary = "INSERT INTO {}.virtual_dictionaries (name, short_desc) " \
                                "VALUES (%s, %s);"

select_vdict_id = "SELECT id FROM {}.virtual_dictionaries WHERE name = %s;"

prepare_insert_virtual_dictionary_items = "PREPARE insert_virtual_dictionary_items(VARCHAR(32)) AS " \
                                            "INSERT INTO {0}.virtual_dictionary_items (virt_id, dict_id) " \
                                                "VALUES (%s, (" \
                                                    "SELECT id FROM {0}.dictionaries WHERE name = $1)" \
                                                    ");"

execute_insert_virtual_dictionary_items = "EXECUTE insert_virtual_dictionary_items(%s);"

script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} [-f conf_file] del virt_name", file=sys.stderr)
    print("Adds virtual dictionaries in pgsql.", file=sys.stderr)

def add_vdict(cur, schema, name, short_desc, dict_names):
    cur.execute(insert_virtual_dictionary.format(schema), (name, short_desc))
    cur.execute(select_vdict_id.format(schema), (name, ))
    virt_id = cur.fetchone()[0]
    cur.execute(prepare_insert_virtual_dictionary_items.format(schema), (virt_id, ))
    for dict_name in dict_names:
        cur.execute(execute_insert_virtual_dictionary_items, (dict_name, ))

args = pgutil.get_pgsql_params(None, -1, usage)

if len(args) < 2:
    usage()
    sys.exit(2)

cmd_cased, virt_name, *cmd_args = args
cmd = cmd_cased.lower()

if len(cmd_args) < 2:
    usage()
    sys.exit(2)
short_desc, *dict_names = cmd_args
pgutil.process_pgsql_task(add_vdict, virt_name, short_desc, dict_names)
