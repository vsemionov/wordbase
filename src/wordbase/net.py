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


import io
import logging

import log


DICT_EOL = '\r\n'

logger = None


def init():
    global logger
    logger = logging.getLogger(__name__)

def net_exc(func):
    def wrap_net_exc(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            logger.error(ex)
            raise ex
    return wrap_net_exc

class Connection:
    def __init__(self, sock):
        self._sio = sock.makefile(mode="rw", encoding="utf-8", newline='')

    @net_exc
    def read_line(self):
        """reads a line of input
        
        The trailing EOL is stripped.
        
        throws socket.timeout, EOFError, BufferError
        """

        buff = io.StringIO(newline='\n')
        count = 0
        have_cr = False

        while count < 1024:
            ch = self._sio.read(1)
            if not ch:
                raise EOFError("connection closed by client")
            buff.write(ch)
            count += 1

            if ch == '\n' and have_cr:
                line = buff.getvalue()[:-2]
                log.trace_client(line)
                return line
            have_cr = ch == '\r'
        else:
            raise BufferError("maximum command line length exceeded by client")

    @staticmethod
    def _split_line(line):
        l = len(line)
        i = 0
        while i < l:
            n, pre = (1022, '') if line[i] != '.' else (1021, '.')
            chunk = ''.join((pre, line[i:i+n]))
            i += n
            yield chunk
        else:
            if l == 0:
                yield line

    @classmethod
    def _trunc_line(cls, line):
        return next(cls._split_line(line))

    def _write(self, line):
        data = ''.join((line, DICT_EOL))
        self._sio.write(data)
        self._sio.flush()
        log.trace_server(line)

    @net_exc
    def write_line(self, line, split=True):
        """writes a line of output
        
        The line argument should not end with an EOL.
        The first leading '.' char is doubled.
        If split is True, lines with above-maximum length are split to multiple lines.
        If split is False, lines with above-maximum length are truncated.
        """

        if split:
            for subline in self.__class__._split_line(line):
                self._write(subline)
        else:
            self._write(self.__class__._trunc_line(line))

    @net_exc
    def write_status(self, code, message):
        line = "{:03d} {:s}".format(code, message)
        self.write_line(line, split=False)

    @net_exc
    def write_text_end(self):
        self._write('.')

    @net_exc
    def write_text(self, lines):
        for line in lines:
            self.write_line(line)
        self.write_text_end()

    @net_exc
    def close(self):
        self._sio.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
