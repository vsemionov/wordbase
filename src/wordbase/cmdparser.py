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

from pyparsing import ParseException, ParserElement, Empty, White, Suppress, CharsNotIn, Combine, ZeroOrMore, OneOrMore, Optional, StringStart, StringEnd, Word, nums

import modules
import debug


logger = logging.getLogger(__name__)

CTL = ''.join(chr(i) for i in range(0, 32)) + chr(127)
WS = " \t"

ParserElement.setDefaultWhitespaceChars(WS)

_ws = White(WS)

_quoted_pair = Suppress('\\') + CharsNotIn("", exact=1)
_dqtext = CharsNotIn("\"\\" + CTL, exact=1)
_dqstring = Combine(Suppress('"') + ZeroOrMore(_dqtext | _quoted_pair) + Suppress('"'))
_sqtext = CharsNotIn("'\\" + CTL, exact=1)
_sqstring = Combine(Suppress('\'') + ZeroOrMore(_sqtext | _quoted_pair) + Suppress('\''))

_atom = Empty() + CharsNotIn(" '\"\\" + CTL)
_string = Combine(OneOrMore(_dqstring | _sqstring | _quoted_pair))
_word = Combine(OneOrMore(_atom | _string))

_ws_state = ""

def _ws_action(t):
    global _ws_state
    _ws_state = t[0]
    return ""

def _word_action(t):
    global _ws_state
    if _ws_state:
        r = ''.join((_ws_state, t[0]))
        _ws_state = ""
        return r

def _text_action(t):
    global _ws_state
    _ws_state = ""

_text = Combine(OneOrMore(_word.copy().setParseAction(_word_action) | _ws.copy().setParseAction(_ws_action))).setParseAction(_text_action)
_description = _text.copy()


_cmd_found = None

def _get_keyword_action(kw):
    def _keyword_action(s, l, t):
        if t[0].upper() != kw.upper():
            raise ParseException(s, l, "expected \"{}\"".format(kw))
        return kw
    return _keyword_action

def _keyword(kw):
    return _word.copy().setParseAction(_get_keyword_action(kw))

def _get_cmd_action(cmd):
    def _cmd_action(s, l, t):
        global _cmd_found
        _cmd_found = cmd
    return _cmd_action

_start = StringStart()
_end = StringEnd()

def _command(name, real=None):
    cmd = _keyword(name) if name else Empty()
    return cmd.addParseAction(_get_cmd_action(real or name))

def _shortcut(s):
    return Empty().addParseAction(lambda t: s)

def _reset_cmd_action(t):
    global _cmd_found
    _cmd_found = None

_reset_command = Empty().setParseAction(_reset_cmd_action)

def _command_string(body):
    if debug.enabled:
        body |= _command("T") + Word(nums).setParseAction(lambda t: int(t[0])) + _reset_command + body
    return _start + body + _end


_show_db = _keyword("DB") | _keyword("DATABASES")
_show_strat = _keyword("STRAT") | _keyword("STRATEGIES")
_show_info = _keyword("INFO") + _word
_show_server = _keyword("SERVER")

_show_params = _show_db | _show_strat | _show_info | _show_server

_grammar = _command_string(_command(""))
_grammar |= _command_string(_command("DEFINE") + _word + _word) | _command_string(_command("D", "DEFINE") + _shortcut("*") + _word) | _command_string(_command("D", "DEFINE") + _word + _word)
_grammar |= _command_string(_command("MATCH") + _word + _word + _word) | _command_string(_command("M", "MATCH") + _shortcut("*") + _shortcut(".") + _word) | _command_string(_command("M", "MATCH") + _shortcut("*") + _word + _word) | _command_string(_command("M", "MATCH") + _word + _word + _word)
_grammar |= _command_string(_command("SHOW") + _show_params)
_grammar |= _command_string(_command("CLIENT") + Optional(_text, default=""))
_grammar |= _command_string(_command("STATUS")) | _command_string(_command("S", "STATUS"))
_grammar |= _command_string(_command("HELP")) | _command_string(_command("H", "HELP"))
_grammar |= _command_string(_command("QUIT")) | _command_string(_command("Q", "QUIT"))
_grammar |= _command_string(_command("OPTION") + _keyword("MIME"))
_grammar |= _command_string(_command("AUTH") + Optional(_text)) # not supported, therefore defined liberally
_grammar |= _command_string(_command("SASLAUTH") + Optional(_text)) # not supported, therefore defined liberally
_grammar |= _command_string(_command("SASLRESP") + Optional(_text)) # not supported, therefore defined liberally

_grammar.parseWithTabs()


_parser_lock = modules.mp().Lock()


def parse_command(line):
    with _parser_lock:
        try:
            results = _grammar.parseString(line)
            logger.debug("parser results: %s", results)
            return True, results
        except ParseException as pe:
            logger.debug(pe)
            return False, _cmd_found
