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

import psycopg2

import db


logger = logging.getLogger(__name__)


def configure(config):
    global _host, _port, _user, _password, _database, _schema
    _host = config.get("host", "localhost")
    _port = config.getint("port", 5432)
    _user = config.get("user", "nobody")
    _password = config.get("password", "")
    _database = config.get("database", "wordbase")
    _schema = config.get("schema", "") or "public"

    logger.debug("initialized")


def _statement(stmt):
    return stmt.format(_schema)

def pg_exc(func):
    def wrap_pg_exc(*args):
        try:
            return func(*args)
        except (psycopg2.Error, psycopg2.Warning) as ex:
            raise db.BackendError(ex)
    return wrap_pg_exc

class Backend(db.BackendBase):
    def __init__(self):
        self._conn = None
        self._cur = None

    @pg_exc
    def connect(self):
        self.close()
        self._conn = psycopg2.connect(host=_host, port=_port, user=_user, password=_password, database=_database)
        self._conn.autocommit = True
        self._cur = self._conn.cursor()
        logger.debug("connected to pgsql")

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
    def get_dictionaries(self):
        cur = self._cur
        stmt = "SELECT name, short_desc FROM {}.dictionaries ORDER BY (virt_id IS NULL) DESC, db_order;".format(_schema)
        cur.execute(stmt)
        rs = cur.fetchall()
        return rs

    @pg_exc
    def get_real_dictionary_names(self):
        cur = self._cur
        stmt = "SELECT name FROM {}.dictionaries WHERE virt_id IS NULL ORDER BY db_order;".format(_schema)
        cur.execute(stmt)
        rs = cur.fetchall()
        return list(zip(*rs))[0]

    @staticmethod
    def _invalid_dict(dictionary):
        raise db.InvalidDictionaryError("invalid dictionary: {}".format(dictionary))

    @pg_exc
    def get_dictionary_info(self, dictionary):
        cur = self._cur
        stmt = "SELECT name, (virt_id IS NOT NULL) AS virtual, info FROM {}.dictionaries WHERE name = %s AND (dict_id IS NOT NULL OR virt_id IS NOT NULL);".format(_schema)
        cur.execute(stmt, (dictionary,))
        if cur.rowcount < 1:
            self.__class__._invalid_dict(dictionary)
        row = cur.fetchone()
        return row

    def _get_ids(self, dictionary):
        cur = self._cur
        stmt = "SELECT dict_id, virt_id FROM {}.dictionaries WHERE name = %s;".format(_schema)
        cur.execute(stmt, (dictionary,))
        if cur.rowcount >= 1:
            ids = cur.fetchone()
            dict_id, virt_id = ids
            if dict_id is not None or virt_id is not None:
                return ids
        self.__class__._invalid_dict(dictionary)

    def _get_words_real(self, dict_id):
        cur = self._cur
        stmt = "SELECT DISTINCT word FROM {}.definitions WHERE dict_id = %s;".format(_schema)
        cur.execute(stmt, (dict_id,))
        rs = cur.fetchall()
        return list(zip(*rs))[0]

    def _get_virt_dict(self, virt_id):
        cur = self._cur
        stmt = "SELECT {0}.virtual_dictionaries.dict_id, {0}.dictionaries.name FROM {0}.virtual_dictionaries INNER JOIN {0}.dictionaries USING dict_id WHERE {0}.virtual_dictionaries.virt_id = %s ORDER BY {0}.dictionaries.db_order;".format(_schema)
        cur.execute(stmt, (virt_id,))
        rs = cur.fetchall()
        return rs

    @pg_exc
    def get_words(self, dictionary):
        dict_id, virt_id = self._get_ids(dictionary)
        if dict_id is not None:
            words = self._get_words_real(dict_id)
            res = [(dictionary, words)]
            return res
        else:
            res = []
            for dict_id, dict_name in self._get_virt_dict(virt_id):
                words = self._get_words_real(dict_id)
                res += (dict_name, words)
            return res

    @pg_exc
    def get_virtual_dictionary(self, dictionary):
        dict_id, virt_id = self._get_ids(dictionary)
        del dict_id
        if virt_id is None:
            self.__class__._invalid_dict(dictionary)
        virt_dict = self._get_virt_dict(virt_id)
        return virt_dict
