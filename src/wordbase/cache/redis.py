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

import cache


logger = None

_servers = []
_ttl = 0


def configure(config):
    global _servers, _ttl
    _ttl = config.getint("ttl", 0)
    servers = config.get("servers", "")
    for server in servers.split(','):
        server = servers.strip()
        if not server:
            raise ValueError("invalid redis connection string format")
        parts = server.split('@')
        if len(parts) == 1:
            password = None
        else:
            password = '@'.join(parts[:-1])
        address = parts[-1]
        parts = address.split(':')
        if len(parts) == 1:
            port = 6379
        elif len(parts) == 2:
            port = int(parts[1])
        else:
            raise ValueError("invalid redis connection string format")
        host = parts[0]
        servers.append((host, port, password))

    global logger
    logger = logging.getLogger(__name__)
    logger.debug("initialized")


class Cache(cache.CacheBase):
    def connect(self):
        pass

    def close(self):
        pass

    def get(self, key):
        return None

    def set(self, key, value):
        pass
