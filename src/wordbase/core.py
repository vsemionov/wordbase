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


import socket
import logging
import random
import time

import modules
import net
import cmdparser
import helpmsg
import db
import match
import debug


logger = logging.getLogger(__name__)

STOP_DICT_NAME = "--exit--"

_server_string = None
_domain = None


def _escaped(s):
    return s.replace('\\', "\\\\").replace('"', "\\\"")

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
    dbs = backend.get_dictionaries()
    n = len(dbs)
    if n:
        conn.write_status(110, "{} databases present - text follows".format(n))
        for db in dbs:
            name, short_desc = db
            line = "{} \"{}\"".format(name, _escaped(short_desc))
            conn.write_line(line)
        conn.write_text_end()
        conn.write_status(250, "ok")
    else:
        conn.write_status(554, "No databases present")

def _show_strat(conn):
    _not_implemented(conn)

def _show_info(conn, backend, database):
    _not_implemented(conn)

def _show_server(conn):
    _not_implemented(conn)

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

def _handle_match(conn, backend, command):
    _not_implemented(conn)

def _handle_define(conn, backend, command):
    _not_implemented(conn)

def _handle_time_command(conn, backend, command):
    start = time.clock()
    null_conn = debug.NullConnection()
    n = command[1]
    subcmd = command[2]
    for i in range(n):
        _handle_command(null_conn, subcmd)
    del i
    end = time.clock()
    elapsed = end - start

    _handle_command(conn, backend, subcmd)

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


def _send_banner(conn):
    fqdn = socket.getfqdn()
    local = "{}.{}".format(random.randint(0, 9999), random.randint(0, 9999))
    msg_id = "<{}@{}>".format(local, _domain)
    conn.write_status(220, "{} {} {}".format(fqdn, _server_string, msg_id))

def _handle_syntax_error(conn, command):
    if command is None:
        code, msg = 500, "Syntax error, command not recognized"
    else:
        code, msg = 501, "Syntax error, illegal parameters"
    conn.write_status(code, msg)

def _handle_command(conn, backend, command):
    name = command[0]
    handler = _cmd_handlers.get(name, _not_implemented)
    return handler(conn, backend, command)

def _session(conn):
    try:
        with modules.db().Backend() as backend:
            _send_banner(conn)

            end = False
            while not end:
                line = conn.read_line()
                correct, command = cmdparser.parse_command(line)
                if correct:
                    end = _handle_command(conn, backend, command)
                else:
                    _handle_syntax_error(conn, command)
    except db.BackendError as be:
        logger.error(be)
        conn.write_status(420, "Server temporarily unavailable")
    except (IOError, EOFError, UnicodeDecodeError, BufferError) as ex:
        logger.error(ex)
    except Exception as ex:
        logger.exception("unexpected error")

def configure(config):
    global _server_string, _domain
    _server_string = config.get("server", "wordbase")
    _domain = config.get("domain", "example.com")

def process_session(sock, addr):
    with sock, net.Connection(sock) as conn:
        host, port = addr
        logger.info("session started from address %s:%d", host, port)
        try:
            _session(conn)
        finally:
            logger.info("session ended")
