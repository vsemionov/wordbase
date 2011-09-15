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


def get_default_conf_path():
    return "/etc/wordbase.conf"

def get_pgsql_params(fmt, nargs, usage):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:" + (fmt or ""))
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if len(args) != nargs:
        usage()
        sys.exit(2)

    conf_path = None
    for opt, arg in opts:
        if opt == "-f":
            conf_path = arg

    if conf_path is None:
        conf_path = get_default_conf_path()

    with open(conf_path) as conf:
        config = configparser.ConfigParser(inline_comment_prefixes="#")
        config.read_file(conf, conf_path)

    pgconfig = config["pgsql"]

    host = pgconfig.get("host", "localhost")
    port = pgconfig.getint("port", 5432)
    user = pgconfig.get("user", "nobody")
    password = pgconfig.get("password", "")
    database = pgconfig.get("database", "wordbase")
    schema = pgconfig.get("schema", "") or "public"

    return host, port, user, password, database, schema, args
