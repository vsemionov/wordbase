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


import logging
import time

import helpmsg
import db
import match
import debug


logger = logging.getLogger(__name__)

STOP_DB_NAME = "--exit--"

_server_string = ""
_server_info = ""


def handle_550(func):
    def wrapper(conn, *args):
        try:
            func(conn, *args)
        except db.InvalidDatabaseError as ide:
            logger.debug(ide)
            conn.write_status(550, "Invalid database, use \"SHOW DB\" for list of databases")
    return wrapper

def _validate_db_name(name):
    if name == STOP_DB_NAME:
        db.BackendBase.invalid_db(name)

def _escaped(s):
    return s.replace('\\', "\\\\").replace('"', "\\\"")

def _send_text(conn, text):
    lines = text.splitlines()
    for line in lines:
        conn.write_line(line)

def _null_handler(*args):
    pass

def _not_implemented(conn, *args):
    conn.write_status(502, "Command not implemented")

def _handle_quit(conn, *args):
    conn.write_status(221, "Closing Connection")
    return True

def _handle_help(conn, *args):
    conn.write_status(113, "help text follows")
    conn.write_text(helpmsg.help_lines)
    conn.write_status(250, "ok")

def _handle_status(conn, *args):
    conn.write_status(210, "up")

def _handle_client(conn, backend, command):
    logger.info("client: %s", command[1])
    conn.write_status(250, "ok")

def _show_db(conn, backend):
    dbs = backend.get_databases()
    n = len(dbs)
    if n:
        conn.write_status(110, "{} databases present - text follows".format(n))
        dbs.sort(key=lambda t: t[1])
        for db in dbs:
            name, virtual, short_desc = db
            del virtual
            line = "{} \"{}\"".format(name, _escaped(short_desc))
            conn.write_line(line)
        conn.write_text_end()
        conn.write_status(250, "ok")
    else:
        conn.write_status(554, "No databases present")

def _show_strat(conn):
    _not_implemented(conn)

@handle_550
def _show_info(conn, backend, database):
    virtual, info = backend.get_database_info(database)
    conn.write_status(112, "database information follows")
    if info:
        _send_text(conn, info)
    elif virtual:
        names = backend.get_virtual_database(database)
        for name in names:
            virtual, info = backend.get_database_info(database)
            conn.write_line("================ {} ================".format(name))
            if info:
                _send_text(conn, info)
    conn.write_text_end()
    conn.write_status(250, "ok")

def _show_server(conn):
    info = open(_server_info) if _server_info else None
    try:
        conn.write_status(114, "server information follows")
        conn.write_line(_server_string)
        if info:
            for line in info:
                conn.write_line(line.rstrip('\n'))
    finally:
        if info:
            info.close()
    conn.write_text_end()
    conn.write_status(250, "ok")

def _handle_show(conn, backend, command):
    param = command[1]
    if param in ["DB", "DATABASES"]:
        _show_db(conn, backend)
    elif param in ["STRAT", "STRATEGIES"]:
        _show_strat(conn)
    elif param == "INFO":
        database = command[2]
        _show_info(conn, backend, database)
    elif param == "SERVER":
        _show_server(conn)
    else:
        assert False, "unhandled SHOW command"

@handle_550
def _handle_match(conn, backend, command):
    database = command[1]
    strategy = command[2]
    word = command[3]
    _validate_db_name(database)
    _not_implemented(conn)

@handle_550
def _handle_define(conn, backend, command):
    def get_matches(db_name):
        ml = []
        virtual, short_desc = dbs[db_name]
        del short_desc
        if not virtual:
            words = strat(word, backend.get_words(db_name))
            matches = [(wd, []) for wd in words]
            ml = [(db_name, matches)]
        else:
            for name in backend.get_virtual_database(db_name):
                words = strat(word, backend.get_words(name))
                matches = [(wd, []) for wd in words]
                ml.append((name, matches))
        return ml

    database = command[1]
    word = command[2]
    _validate_db_name(database)
    strat = match.get_strategy("exact")

    dbs = {name: (virtual, short_desc) for (name, virtual, short_desc) in backend.get_databases()}

    db_match_defs = []
    if database in ("*", "!"):
        for db in dbs:
            name, virtual, short_desc = db
            if virtual:
                continue
            if name == STOP_DB_NAME:
                break
            ml = get_matches(name)
            assert len(ml) == 1, "virtual database detected"
            db_match_defs.extend(ml)
            if database == "!":
                name, matches = ml[0]
                if len(matches):
                    break
    else:
        ml = get_matches(database)
        db_match_defs.extend(ml)

    num_defs = 0

    for name, matches in db_match_defs:
        for wd, defs in matches:
            res = backend.get_definitions(name, wd)
            defs.extend(res)
            num_defs += len(res)

    if not num_defs:
        conn.write_status(552, "No match")
        return

    conn.write_status(150, "{} definitions retrieved - definitions follow".format(num_defs))

    for name, matches in db_match_defs:
        virtual, short_desc = dbs[name]
        escaped_short_desc = _escaped(short_desc)
        for wd, defs in matches:
            escaped_word = _escaped(wd)
            for definition in defs:
                conn.write_status(151, "\"{}\" {} \"{}\" - text follows".format(escaped_word, name, escaped_short_desc))
                _send_text(conn, definition)
                conn.write_text_end()

    conn.write_status(250, "ok")

def _handle_time_command(conn, backend, command):
    start = time.clock()
    null_conn = debug.NullConnection()
    n = command[1]
    subcmd = command[2]
    for i in range(n):
        handle_command(null_conn, backend, subcmd)
    if n: del i
    end = time.clock()
    elapsed = end - start

    handle_command(conn, backend, subcmd)

    conn.write_status(280, "time: {:.3f} s".format(elapsed))


_cmd_handlers = {
                 "": _null_handler,
                 "DEFINE": _handle_define,
                 "MATCH": _handle_match,
                 "SHOW": _handle_show,
                 "CLIENT": _handle_client,
                 "STATUS": _handle_status,
                 "HELP": _handle_help,
                 "QUIT": _handle_quit,
                 "T": _handle_time_command
                }


def handle_syntax_error(conn, command):
    if command is None:
        code, msg = 500, "Syntax error, command not recognized"
    else:
        code, msg = 501, "Syntax error, illegal parameters"
    conn.write_status(code, msg)

def handle_command(conn, backend, command):
    name = command[0]
    handler = _cmd_handlers.get(name, _not_implemented)
    return handler(conn, backend, command)

def configure(server_string, server_info):
    global _server_string, _server_info
    _server_string = server_string
    _server_info = server_info
