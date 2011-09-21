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
import re

import psycopg2

import pgutil


script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} [-f conf_file] [-o db_order] [-i info_file] name short_desc dict_file".format(script_name), file=sys.stderr)
    print("Imports a bedic dictionary into pgsql.", file=sys.stderr)


options, (name, short_desc, dict_file) = pgutil.get_pgsql_params("o:i:", 3, 3, usage)

db_order = options.get("-o")
if db_order is not None:
    db_order = int(db_order)

info_file = options.get("-i")

if info_file is not None:
    with open(info_file, encoding="utf-8") as f:
        info = f.read()
else:
    info = None

defs = []

transcription = re.compile(r"^(\[[^\[\]\n]+\]) {2}", re.MULTILINE)

with open(dict_file, encoding="cp1251") as f:
    for item in f.read().split('\0')[1:-1]:
        word, definition = item.split('\n', 1)
        definition = transcription.sub(r"\1\n", definition)
        defs.append((word, definition))

pgutil.process_pgsql_task(pgutil.import_task, db_order, name, short_desc, info, defs)
