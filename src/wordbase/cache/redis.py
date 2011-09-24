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
import logging

import redis

import debug
import cache


logger = None

_servers = []
_timeout = 0
_ttl = 0


def configure(config):
    global _servers, _timeout, _ttl

    servers = config.get("servers", "")
    for server in servers.split(','):
        server = servers.strip()
        if not server:
            continue

        parts = server.split('@')
        if len(parts) == 1:
            password = None
        else:
            password = '@'.join(parts[:-1])

        database = parts[-1]
        parts = database.split(':')
        if len(parts) == 1:
            db = 0
        elif len(parts) == 2:
            db = int(parts[1])
        else:
            raise ValueError("invalid redis connection string format")

        address = parts[0]

        parts = address.split(':')
        if len(parts) == 1:
            port = 6379
        elif len(parts) == 2:
            port = int(parts[1])
        else:
            raise ValueError("invalid redis connection string format")
        host = parts[0]

        _servers.append((host, port, db, password))

    if not len(_servers):
        raise ValueError("no redis connection strings specified")

    _timeout = config.getint("timeout", 15) or None
    _ttl = config.getint("ttl", 0)

    global logger
    logger = logging.getLogger(__name__)
    logger.debug("initialized")


def redis_exc(func):
    def wrap_redis_exc(*args):
        try:
            return func(*args)
        except redis.RedisError as ex:
            exc_info = sys.exc_info() if debug.enabled else None
            logger.error(ex, exc_info=exc_info)
            raise cache.CacheError(ex)
    return wrap_redis_exc

class Cache(cache.CacheBase):
    def __init__(self):
        self._databases = [redis.Redis(host=host, port=port, db=db, password=password, socket_timeout=_timeout) for (host, port, db, password) in _servers]
        self._pipelines = [database.pipeline() for database in self._databases] if _ttl else None

    @redis_exc
    def connect(self):
        try:
            for idx, db in enumerate(self._databases):
                pool = db.connection_pool
                conn = pool.get_connection(None)
                conn.connect()
                pool.release(conn)
                logger.debug("connected to redis {}".format(idx))
        except Exception as ex:
            try:
                self.close()
            except Exception:
                pass
            raise ex

    @redis_exc
    def close(self):
        first_ex = None
        for idx, db in enumerate(self._databases):
            try:
                pool = db.connection_pool
                pool.disconnect()
                logger.debug("closed redis connection {}".format(idx))
            except Exception as ex:
                if first_ex is None:
                    first_ex = ex
        if first_ex is not None:
            raise first_ex

    @staticmethod
    def _get_db_idx(key):
        db_idx = hash(key) % len(_servers)
        return db_idx

    @redis_exc
    def get(self, key):
        db_idx = self.__class__._get_db_idx(key)
        db = self._databases[db_idx]
        value = db.get(key)
        return value

    @redis_exc
    def set(self, key, value):
        db_idx = self.__class__._get_db_idx(key)
        if not _ttl:
            db = self._databases[db_idx]
            db.set(key, value)
        else:
            pipe = self._pipelines[db_idx]
            pipe.set(key, value)
            pipe.expire(key, _ttl)
            pipe.execute()
