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


create_schema = "CREATE SCHEMA {};"

create_dictionaries = "CREATE TABLE {}.dictionaries (" \
                        "id SERIAL PRIMARY KEY, " \
                        "dict_id SERIAL UNIQUE, " \
                        "virt_id SERIAL UNIQUE, " \
                        "db_order INTEGER, " \
                        "name VARCHAR(32) UNIQUE NOT NULL CHECK (name ~ '^[^ ''\"\\\\\\\\]+$'), " \
                        "short_desc VARCHAR(128) NOT NULL, " \
                        "info TEXT, " \
                        "CHECK ((dict_id IS NOT NULL AND virt_id IS NULL) OR (dict_id IS NULL AND virt_id IS NOT NULL AND info IS NULL))" \
                        ");"

create_definitions = "CREATE TABLE {0}.definitions (" \
                        "id SERIAL PRIMARY KEY, " \
                        "dict_id INTEGER NOT NULL REFERENCES {0}.dictionaries(dict_id), " \
                        "word VARCHAR(64) NOT NULL, " \
                        "definition TEXT NOT NULL" \
                        ");"

create_virtual_dictionaries = "CREATE TABLE {0}.virtual_dictionary_items (" \
                                    "virt_id INTEGER NOT NULL REFERENCES {0}.dictionaries(virt_id), " \
                                    "dict_id INTEGER NOT NULL REFERENCES {0}.dictionaries(dict_id), " \
                                    "PRIMARY KEY (virt_id, dict_id)" \
                                    ");" \

script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} [-f conf_file]".format(script_name), file=sys.stderr)
    print("Initializes a wordbase pgsql schema.", file=sys.stderr)

def init_pgsql_task(cur, schema):
    if schema != "public":
        cur.execute(create_schema.format(schema))
    cur.execute(create_dictionaries.format(schema))
    cur.execute(create_definitions.format(schema))
    cur.execute(create_virtual_dictionaries.format(schema))


pgutil.get_pgsql_params(None, 0, usage)

pgutil.process_pgsql_task(init_pgsql_task)
