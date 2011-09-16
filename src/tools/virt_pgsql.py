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


insert_dictionary = "INSERT INTO {}.dictionaries (dict_id, db_order, name, short_desc, info) " \
                                "VALUES (NULL, %s, %s, %s, %s);"

select_virt_id = "SELECT virt_id FROM {}.dictionaries WHERE name = %s;"

prepare_insert_virtual_dictionary = "PREPARE insert_virtual_dictionary(VARCHAR(32)) AS " \
                                        "INSERT INTO {0}.virtual_dictionaries (virt_id, dict_id) " \
                                            "VALUES (%s, (" \
                                                "SELECT dict_id FROM {0}.dictionaries WHERE name = $1)" \
                                                ");"

execute_insert_virtual_dictionary = "EXECUTE insert_virtual_dictionary(%s);"

script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} [-f conf_file] virt_name short_desc dict_name [...]", file=sys.stderr)
    print("Adds virtual dictionaries in pgsql.", file=sys.stderr)

def add_vdict(cur, schema, db_order, virt_name, short_desc, info, dict_names):
    cur.execute(insert_dictionary.format(schema), (db_order, virt_name, short_desc, info))
    cur.execute(select_virt_id.format(schema), (virt_name, ))
    virt_id = cur.fetchone()[0]
    cur.execute(prepare_insert_virtual_dictionary.format(schema), (virt_id, ))
    for dict_name in dict_names:
        cur.execute(execute_insert_virtual_dictionary, (dict_name, ))

options, args = pgutil.get_pgsql_params("o:i:", 3, None, usage)

if len(args) < 3:
    usage()
    sys.exit(2)

db_order = options.get("-o")
if db_order is not None:
    db_order = int(db_order)

info_file = options.get("-i")

virt_name, short_desc, *dict_names = args

if info_file is not None:
    with open(info_file, encoding="utf-8") as f:
        info = f.read()
else:
    info = None

pgutil.process_pgsql_task(add_vdict, db_order, virt_name, short_desc, info, dict_names)
