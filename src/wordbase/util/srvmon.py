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


import threading
import itertools
import socket
import time
import random
import logging


logger = None


def init():
    global logger
    logger = logging.getLogger(__name__)


def _log_status(address, status):
    host, port = address
    if status:
        logger.info("server {}:{} is up".format(host, port))
    else:
        logger.warning("server {}:{} is down".format(host, port))

class _HeartbeatThread(threading.Thread):
    def __init__(self, statuses, index, address, timeout):
        super().__init__()
        self.daemon = True

        self._statuses = statuses
        self._index = index
        self._address = address
        self._timeout = timeout

    def run(self):
        init_sleep = random.random() * 1.0
        time.sleep(init_sleep)
        while True:
            try:
                sock = socket.create_connection(self._address, self._timeout)
                sock.close()
                status = True
            except socket.error:
                status = False
            if self._statuses[self._index] != status:
                # ignoring the race condition here, because it is not important
                _log_status(self._address, status)
            self._statuses[self._index] = status
            time.sleep(1.0)

class ServerMonitor():
    def __init__(self, servers, timeout):
        timeout = timeout or 15
        self._servers = list(servers)
        self._statuses = [True for server in servers]

    def get_server_index(self, key):
        compressor = itertools.compress(self._servers, self._statuses)
        avail_list = list(compressor)
        navail = len(avail_list)
        if navail == 0:
            return None
        avail_index = hash(key) % navail
        server = avail_list[avail_index]
        server_index = self._servers.index(server)
        return server_index

    def notify_server_down(self, index):
        _log_status(self._servers[index], False)
        self._statuses[index] = False
