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

import net
import parser


logger = logging.getLogger(__name__)


def _banner(sio):
    msg_id = "<!@*>"
    net.write_status(sio, 220, "Welcome! {}".format(msg_id))

def _handle_syntax_error(sio, command):
    pass

def _handle_command(sio, command):
    pass

def _session(sock):
    with net.get_sio(sock) as sio:
        try:
            _banner(sio)

            end = False
            while not end:
                line = net.read_line(sio)
                correct, command = parser.parse_command(line)
                if correct:
                    end = _handle_command(sio, command)
                else:
                    _handle_syntax_error(sio, command)
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
