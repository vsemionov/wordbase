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

import log


DICT_EOL = '\r\n'


def get_sio(sock):
    sio = sock.makefile(mode="rw", encoding="utf-8", newline=DICT_EOL)
    return sio

def read_line(sio):
    """reads a line of input
    
    The trailing EOL is stripped.
    
    throws socket.timeout, EOFError, BufferError
    """

    buff = io.StringIO(newline=DICT_EOL)
    count = 0
    have_cr = False

    while count < 1024:
        ch = sio.read(1)
        if not ch:
            raise EOFError("client closed the connection prematurely")
        buff.write(ch)
        count += 1

        if ch == '\n' and have_cr:
            line = buff.getvalue().rstrip("\n")
            log.trace_client(line)
            return line
        have_cr = ch == '\r'
    else:
        raise BufferError("client exceeded the maximum command line length")

def _split_line(line):
    l = len(line)
    i = 0
    while i < l:
        n, pre = (1022, '') if line[i] != '.' else (1021, '.')
        chunk = ''.join((pre, line[i:i+n]))
        i += n
        yield chunk

def _trunc_line(line):
    return next(_split_line(line))

def _write(sio, line):
    data = ''.join((line, DICT_EOL))
    sio.write(data)
    sio.flush()
    log.trace_server(line)

def write_line(sio, line, split=True):
    """writes a line of output
    
    The line argument should not end with an EOL.
    The first leading '.' char is doubled.
    If split is True, lines with above-maximum length are split to multiple lines.
    If split is False, lines with above-maximum length are truncated.
    """

    if split:
        for subline in _split_line(line):
            _write(sio, subline)
    else:
        _write(sio, _trunc_line(line))

def write_status(sio, code, message):
    line = "{:03d} {:s}".format(code, message)
    write_line(sio, line, split=False)

def write_text_end(sio):
    _write(sio, '.')

def write_text(sio, lines):
    for line in lines:
        write_line(sio, line)
    write_text_end(sio)
