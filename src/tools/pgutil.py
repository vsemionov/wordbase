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
import getopt
import configparser

import psycopg2


_host = _port = _user = _password = _database = _schema = None

_insert_dictionary = "INSERT INTO {}.dictionaries (virt_id, db_order, name, short_desc, info) " \
                        "VALUES (NULL, %s, %s, %s, %s);"

_select_dict_id = "SELECT dict_id FROM {}.dictionaries WHERE name = %s;"

_prepare_insert_definition = "PREPARE insert_definition(VARCHAR, TEXT) AS " \
                                "INSERT INTO {}.definitions (dict_id, word, definition) " \
                                    "VALUES (%s, $1, $2);"

_execute_insert_definition = "EXECUTE insert_definition(%s, %s);"


def get_default_conf_path():
    return "/etc/wordbase.conf"

def get_pgsql_params(fmt, minargs, maxargs, usage):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:" + (fmt or ""))
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if (minargs is not None and len(args) < minargs) or (maxargs is not None and len(args) > maxargs):
        usage()
        sys.exit(2)

    conf_path = None
    options = {}
    for opt, arg in opts:
        if opt == "-f":
            conf_path = arg
        else:
            options[opt] = arg

    if conf_path is None:
        conf_path = get_default_conf_path()

    with open(conf_path) as conf:
        config = configparser.ConfigParser(inline_comment_prefixes="#")
        config.read_file(conf, conf_path)

    pgconfig = config["pgsql"]

    global _host, _port, _user, _password, _database, _schema
    _host = pgconfig.get("host", "localhost")
    _port = pgconfig.getint("port", 5432)
    _user = pgconfig.get("user", "nobody")
    _password = pgconfig.get("password", "")
    _database = pgconfig.get("database", "wordbase")
    _schema = pgconfig.get("schema", "") or "public"

    return options, args

def process_pgsql_task(task, *args):
    conn = psycopg2.connect(host=_host, port=_port, user=_user, password=_password, database=_database)

    try:
        conn.autocommit = False
        cur = conn.cursor()
        try:
            task(cur, _schema, *args)
        finally:
            cur.close()
        conn.commit()
    finally:
        conn.close()

def import_task(cur, schema, db_order, name, short_desc, info, defs, quiet=False):
    cur.execute(_insert_dictionary.format(schema), (db_order, name, short_desc, info))

    cur.execute(_select_dict_id.format(schema), (name, ))
    dict_id = cur.fetchone()[0]

    cur.execute(_prepare_insert_definition.format(schema), (dict_id, ))

    for word, definition in defs:
        cur.execute(_execute_insert_definition, (word, definition))

    if not quiet:
        print("{} definitions imported".format(len(defs)))
