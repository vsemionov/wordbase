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

import db
import modules
import net
import parser


logger = logging.getLogger(__name__)

_help_lines = (
               "DEFINE database word         -- look up word in database",
               "MATCH database strategy word -- match word in database using strategy",
               "SHOW DB                      -- list all accessible databases",
               "SHOW DATABASES               -- list all accessible databases",
               "SHOW STRAT                   -- list available matching strategies",
               "SHOW STRATEGIES              -- list available matching strategies",
               "SHOW INFO database           -- provide information about the database",
               "SHOW SERVER                  -- provide site-specific information",
               "OPTION MIME                  -- use MIME headers",
               "CLIENT info                  -- identify client to server",
               "AUTH user string             -- provide authentication information",
               "STATUS                       -- display timing information",
               "HELP                         -- display this help information",
               "QUIT                         -- terminate connection",
               "",
               "The following commands are unofficial server extensions for debugging",
               "only.  You may find them useful if you are using telnet as a client.",
               "If you are writing a client, you MUST NOT use these commands, since",
               "they won't be supported on any other server!",
               "",
               "D word                       -- DEFINE * word",
               "D database word              -- DEFINE database word",
               "M word                       -- MATCH * . word",
               "M strategy word              -- MATCH * strategy word",
               "M database strategy word     -- MATCH database strategy word",
               "S                            -- STATUS",
               "H                            -- HELP",
               "Q                            -- QUIT",
              )

def _null_handler(sio, command):
    pass

def _not_implemented(sio, command):
    net.write_status(sio, 502, "Command not implemented")

def _handle_quit(sio, command):
    net.write_status(sio, 221, "Closing Connection")
    return True

def _handle_help(sio, command):
    net.write_status(sio, 113, "help text follows")
    net.write_text(sio, _help_lines)
    net.write_status(sio, 250, "ok")

def _handle_status(sio, command):
    net.write_status(sio, 210, "up")

def _handle_client(sio, command):
    net.write_status(sio, 250, "ok")

def _show_db(sio):
    _not_implemented(sio, None)

def _show_strat(sio):
    _not_implemented(sio, None)

def _show_info(sio, database):
    _not_implemented(sio, None)

def _show_server(sio):
    _not_implemented(sio, None)

def _handle_show(sio, command):
    param = command[1]
    if param in ["DB", "DATABASES"]:
        _show_db(sio)
    elif param in ["STRAT", "STRATEGIES"]:
        _show_strat(sio)
    elif param == "INFO":
        database = command[2]
        _show_info(sio, database)
    elif param == "SERVER":
        _show_server(sio)
    else:
        assert False, "unhandled SHOW command"

def _handle_match(sio, command):
    _not_implemented(sio, command)

def _handle_define(sio, command):
    _not_implemented(sio, command)

_cmd_handlers = {
                 "": _null_handler,
                 "DEFINE": _handle_define,
                 "MATCH": _handle_match,
                 "SHOW": _handle_show,
                 "CLIENT": _handle_client,
                 "STATUS": _handle_status,
                 "HELP": _handle_help,
                 "QUIT": _handle_quit,
                 "OPTION": _not_implemented,
                 "AUTH": _not_implemented,
                 "SASLAUTH": _not_implemented,
                 "SASLRESP": _not_implemented,
                }


def _send_banner(sio):
    msg_id = "<!@*>"
    net.write_status(sio, 220, "Welcome! {}".format(msg_id))

def _handle_syntax_error(sio, command):
    if not command:
        code, msg = 500, "Syntax error, command not recognized"
    else:
        code, msg = 501, "Syntax error, illegal parameters"
    net.write_status(sio, code, msg)

def _handle_command(sio, command):
    name = command[0]
    handler = _cmd_handlers[name]
    return handler(sio, command)

def _session(sock):
    with net.get_sio(sock) as sio:
        try:
            with modules.db().Backend() as backend:
                _send_banner(sio)

                end = False
                while not end:
                    line = net.read_line(sio)
                    correct, command = parser.parse_command(line)
                    if correct:
                        end = _handle_command(sio, command)
                    else:
                        _handle_syntax_error(sio, command)
        except db.BackendError as be:
            logger.error(be)
            net.write_status(sio, 420, "Server temporarily unavailable")
        except (IOError, EOFError, UnicodeDecodeError, BufferError) as ex:
            logger.error(ex)
        except Exception as ex:
            logger.exception(ex)

def process_session(sock, addr):
    with sock:
        host, port = addr
        logger.info("session started from address %s:%d", host, port)
        try:
            _session(sock)
        finally:
            logger.info("session ended")
