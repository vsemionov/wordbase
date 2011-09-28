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

import psycopg2 as dbapi

import debug
import db


logger = None

_host = ""
_port = 0
_user = ""
_password = ""
_database = ""
_schema = ""


def configure(config):
    global _host, _port, _user, _password, _database, _schema
    _host = config.get("host", "localhost")
    _port = config.getint("port", 5432)
    _user = config.get("user", "nobody")
    _password = config.get("password", "")
    _database = config.get("database", "wordbase")
    _schema = config.get("schema", "") or "public"

    global logger
    logger = logging.getLogger(__name__)
    logger.debug("initialized")


def _statement(stmt):
    return stmt.format(_schema)

def pg_exc(func):
    def wrap_pg_exc(*args):
        try:
            return func(*args)
        except (dbapi.Error, dbapi.Warning) as ex:
            exc_info = sys.exc_info() if debug.enabled else None
            logger.error(ex, exc_info=exc_info)
            raise db.BackendError(ex)
    return wrap_pg_exc

def pg_conn(func):
    def wrap_pg_conn(self, *args):
        if self._cur is None:
            self._connect_real()
        return func(self, *args)
    return wrap_pg_conn

class Backend(db.BackendBase):
    def __init__(self):
        self._conn = None
        self._cur = None

    def _connect_real(self):
        self.close()
        self._conn = dbapi.connect(host=_host, port=_port, user=_user, password=_password, database=_database)
        self._conn.autocommit = True
        self._cur = self._conn.cursor()
        logger.debug("connected to pgsql")

    @pg_exc
    def connect(self):
        pass

    @pg_exc
    def close(self):
        if self._cur is not None:
            self._cur.close()
            self._cur = None
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.debug("closed the pgsql connection")

    @pg_exc
    @pg_conn
    def get_databases(self):
        cur = self._cur
        stmt = "SELECT name, (virt_id IS NOT NULL) AS virtual, short_desc FROM {}.dictionaries ORDER BY db_order;".format(_schema)
        cur.execute(stmt)
        rs = cur.fetchall()
        return rs

    @pg_exc
    @pg_conn
    def get_database_info(self, database):
        cur = self._cur
        stmt = "SELECT (virt_id IS NOT NULL) AS virtual, info FROM {}.dictionaries WHERE name = %s;".format(_schema)
        cur.execute(stmt, (database,))
        if cur.rowcount < 1:
            self.__class__.invalid_db(database)
        row = cur.fetchone()
        return row

    def _get_ids(self, database):
        cur = self._cur
        stmt = "SELECT dict_id, virt_id FROM {}.dictionaries WHERE name = %s;".format(_schema)
        cur.execute(stmt, (database,))
        if cur.rowcount >= 1:
            ids = cur.fetchone()
            dict_id, virt_id = ids
            if dict_id is not None or virt_id is not None:
                return ids
        self.__class__.invalid_db(database)

    def _get_words_real(self, dict_id):
        cur = self._cur
        stmt = "SELECT DISTINCT word FROM {}.definitions WHERE dict_id = %s ORDER BY word;".format(_schema)
        cur.execute(stmt, (dict_id,))
        rs = cur.fetchall()
        return list(zip(*rs))[0]

    def _get_virt_dict(self, virt_id):
        cur = self._cur
        stmt = "SELECT name FROM {0}.dictionaries INNER JOIN {0}.virtual_dictionaries USING (dict_id) WHERE {0}.virtual_dictionaries.virt_id = %s ORDER BY db_order;".format(_schema)
        cur.execute(stmt, (virt_id,))
        rs = cur.fetchall()
        return list(zip(*rs))[0]

    @pg_exc
    @pg_conn
    def get_words(self, database):
        dict_id, virt_id = self._get_ids(database)
        del virt_id
        if dict_id is None:
            raise db.VirtualDatabaseError("database {} is not real".format(database))
        words = self._get_words_real(dict_id)
        return words

    @pg_exc
    @pg_conn
    def get_virtual_database(self, database):
        dict_id, virt_id = self._get_ids(database)
        del dict_id
        if virt_id is None:
            raise db.VirtualDatabaseError("database {} is not virtual".format(database))
        virt_dict = self._get_virt_dict(virt_id)
        return virt_dict

    @pg_exc
    @pg_conn
    def get_definitions(self, database, word):
        cur = self._cur
        stmt = "SELECT definition FROM {0}.definitions WHERE dict_id = (SELECT dict_id FROM {0}.dictionaries WHERE name = %s) AND word = %s;".format(_schema)
        cur.execute(stmt, (database, word))
        rs = cur.fetchall()
        return list(zip(*rs))[0]
