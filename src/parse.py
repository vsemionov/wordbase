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


from pyparsing import ParserElement, White, Suppress, CharsNotIn, Combine, ZeroOrMore, OneOrMore


CTL = ''.join(chr(i) for i in range(0, 32)) + chr(127)
WS = " \t"

ParserElement.setDefaultWhitespaceChars("")

_ws = White(WS)

_quoted_pair = Suppress('\\') + CharsNotIn("", exact=1)
_dqtext = CharsNotIn("\"\\" + CTL, exact=1)
_dqstring = Combine(Suppress('"') + ZeroOrMore(_dqtext | _quoted_pair) + Suppress('"'))
_sqtext = CharsNotIn("'\\" + CTL, exact=1)
_sqstring = Combine(Suppress('\'') + ZeroOrMore(_sqtext | _quoted_pair) + Suppress('\''))

_atom = CharsNotIn(" '\"\\" + CTL)
_string = Combine(OneOrMore(_dqstring | _sqstring | _quoted_pair))
_word = Combine(OneOrMore(_atom | _string))
_description = Combine(ZeroOrMore(_word | _ws)).setParseAction(lambda t: t[0].strip(WS))
_text = _description.copy()


def parse_command(line):
    pass
