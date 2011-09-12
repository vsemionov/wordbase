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
import signal
import time
import logging


num_children = 0
max_children = 0

logger = logging.getLogger(__name__)


class Lock:
    def _dummy(self, *args):
        pass

    acquire = _dummy
    release = _dummy
    __enter__ = _dummy
    __exit__ = _dummy


def _sigchld_handler(signum, frame):
    logger.debug("caught SIGCHLD; waiting for status")
    pid, status = os.waitpid(-1, os.WNOHANG)
    del status
    if pid:
        global num_children
        num_children -= 1
        logger.debug("child process %d terminated", pid)

def configure(config):
    global max_children
    max_children = int(config["max-clients"])

    signal.signal(signal.SIGCHLD, _sigchld_handler)

    logger.debug("initialized")

def process(task, sock, addr, *args):
    global num_children, max_children

    overload_logged = False
    while num_children >= max_children:
        if not overload_logged:
            logger.warning("max-clients limit reached; waiting for a child to terminate")
            overload_logged = True
        time.sleep(1)

    pid = os.fork()
    if pid == 0:
        logger.debug("process started")
        try:
            task(sock, addr, *args)
        finally:
            logger.debug("process exiting")
        sys.exit()
    else:
        num_children += 1
        sock.close()
