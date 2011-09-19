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

import modules
import net
import cmdparser
import db
import handlers


logger = logging.getLogger(__name__)

_fqdn = ""
_server_string = ""
_domain = ""


def _send_banner(conn):
    local = "{}.{}".format(random.randint(0, 9999), random.randint(0, 9999))
    msg_id = "<{}@{}>".format(local, _domain)
    conn.write_status(220, "{} {} {}".format(_fqdn, _server_string, msg_id))

def _session(conn):
    try:
        with modules.db().Backend() as backend:
            _send_banner(conn)

            end = False
            while not end:
                line = conn.read_line()
                correct, command = cmdparser.parse_command(line)
                if correct:
                    end = handlers.handle_command(conn, backend, command)
                else:
                    handlers.handle_syntax_error(conn, command)
    except db.BackendError as be:
        logger.error(be)
        conn.write_status(420, "Server temporarily unavailable")
    except (IOError, EOFError, UnicodeDecodeError, BufferError) as ex:
        logger.error(ex)
    except Exception as ex:
        logger.exception("unexpected error")

def configure(config):
    global _fqdn, _server_string, _domain
    _fqdn = socket.getfqdn()
    _server_string = config.get("server", "wordbase")
    _domain = config.get("domain", "example.com")

    info = config.get("info", "")
    handlers.configure(_server_string, info)

def process_session(sock, addr):
    with sock, net.Connection(sock) as conn:
        host, port = addr
        logger.info("session started from address %s:%d", host, port)
        try:
            _session(conn)
        finally:
            logger.info("session ended")
