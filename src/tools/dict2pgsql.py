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

script_name = os.path.basename(__file__)


def usage():
    print("Usage: {} [-f conf_file] [-o db_order] [-i info_file] name index_file dict_file".format(script_name), file=sys.stderr)
    print("Imports a dict dictionary into pgsql.", file=sys.stderr)

def decode(encoded):
    s = encoded.rstrip('=')

    num = 0
    cur = 0
    for ch in s:
        c = ord(ch)
        if ord('A') <= c <= ord('Z'):
            cur = c - ord('A')
        elif ord('a') <= c <= ord('z'):
            cur = c - ord('a') + 26
        elif ord('0') <= c <= ord('9'):
            cur = c - ord('0') + 52
        elif ch == '+':
            cur = 62
        elif ch == '/':
            cur = 63
        else:
            raise ValueError("invalid encoding")
        num = (num * 64) + cur

    return num

def read_def(f, offset, size):
    f.seek(offset)
    raw_def = bytes()
    while len(raw_def) < size:
        raw_def += f.read(size - len(raw_def))
    definition = raw_def.decode('utf-8')
    return definition

def is_special(word):
    return word.startswith("00-database-")

options, (name, index_file, dict_file) = pgutil.get_pgsql_params("o:", 3, 3, usage)

db_order = options.get("-o")
if db_order is not None:
    db_order = int(db_order)

short_desc = None
info = None
defs = []

with open(index_file, encoding="utf-8") as index:
    with open(dict_file, "rb") as data:
        for entry in index:
            word, offset, size = entry.strip().split('\t')

            assign = None

            if is_special(word):
                if word == "00-database-short" and short_desc == None:
                    assign = "short_desc"
                elif word == "00-database-info" and info == None:
                    assign = "info"
                elif word == "00-database-8bit-new":
                    print("8-bit encoding is not supported")
                    sys.exit(1)
                else:
                    continue

            offset = decode(offset)
            size = decode(size)

            definition = read_def(data, offset, size)

            if assign:
                globals()[assign] = definition
            else:
                defs.append((word, definition))

pgutil.process_pgsql_task(pgutil.import_task, db_order, name, short_desc, info, defs)
