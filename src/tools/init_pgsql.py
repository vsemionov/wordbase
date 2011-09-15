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


create_schema = "CREATE SCHEMA {};"

create_dictionaries = "CREATE TABLE {}.dictionaries (" \
                        "id SERIAL PRIMARY KEY, " \
                        "match_order INTEGER, " \
                        "name VARCHAR(32) UNIQUE NOT NULL, " \
                        "short_desc VARCHAR(128) NOT NULL, " \
                        "info TEXT NOT NULL" \
                        ");"

create_definitions = "CREATE TABLE {0}.definitions (" \
                        "id SERIAL PRIMARY KEY, " \
                        "dict_id INTEGER NOT NULL REFERENCES {0}.dictionaries, " \
                        "word VARCHAR(64) NOT NULL, " \
                        "definition TEXT NOT NULL" \
                        ");"

create_virtual_dictionaries = "CREATE TABLE {}.virtual_dictionaries (" \
                                "id SERIAL PRIMARY KEY, " \
                                "name VARCHAR(32) UNIQUE NOT NULL, " \
                                "short_desc VARCHAR(128) NOT NULL" \
                                ");" \

create_virtual_dictionary_items = "CREATE TABLE {0}.virtual_dictionary_items (" \
                                    "virt_id INTEGER NOT NULL REFERENCES {0}.virtual_dictionaries, " \
                                    "dict_id INTEGER NOT NULL REFERENCES {0}.dictionaries, " \
                                    "PRIMARY KEY (virt_id, dict_id)" \
                                    ");" \

script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} host[:port] user password database [schema]".format(script_name))
    print("Initializes a wordbase pgsql schema.")

if not 5 <= len(sys.argv) <= 6:
    usage()
    sys.exit(2)

host, *port = sys.argv[1].split(':'); port = int(port[0]) if port else 5432
user = sys.argv[2]
password = sys.argv[3]
database = sys.argv[4]
schema = sys.argv[5] if len(sys.argv) >= 6 else None

conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)

try:
    conn.autocommit = False
    cur = conn.cursor()
    try:
        if schema is not None:
            cur.execute(create_schema.format(schema))
        else:
            schema = "public"
        cur.execute(create_dictionaries.format(schema))
        cur.execute(create_definitions.format(schema))
        cur.execute(create_virtual_dictionaries.format(schema))
        cur.execute(create_virtual_dictionary_items.format(schema))
    finally:
        cur.close()
    conn.commit()
finally:
    conn.close()
