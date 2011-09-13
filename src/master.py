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
import socket
import signal
import errno
import logging

import core


_sock = None

logger = logging.getLogger(__name__)


def _sigterm_handler(signum, frame):
    logger.info("caught SIGTERM; terminating")
    sys.exit()

def _accept_connections(sock, timeout, mp):
    logger.info("waiting for connections")

    while True:
        try:
            conn, addr = sock.accept()

            host, port = addr
            logger.debug("accepted connection from address %s:%d", host, port)

            conn.settimeout(timeout)

            mp.process(core.process_session, conn, addr)
        except IOError as ioe:
            if ioe.errno != errno.EINTR:
                raise

def init(address, backlog):
    logger.info("server starting")

    signal.signal(signal.SIGTERM, _sigterm_handler)

    global _sock
    _sock = socket.socket()
    _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _sock.bind(address)
    _sock.listen(backlog)

    host, port = address
    logger.info("listening at address %s:%d", host, port)

def run(timeout, mp):
    pid = os.getpid()
    try:
        _accept_connections(_sock, timeout, mp)
    finally:
        if os.getpid() == pid:
            logger.info("server stopped")
