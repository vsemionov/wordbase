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

from pyparsing import ParserElement, Empty, Word, CharsNotIn, White, Optional, ZeroOrMore, OneOrMore, StringStart, StringEnd, Combine, Group, Suppress, nums, ParseException 

import debug
import modules


logger = None

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

_text = Combine(OneOrMore(_word.copy().setParseAction(_word_action) | _ws.copy().setParseAction(_ws_action))).setParseAction(_text_action).setFailAction(lambda s, l, ex, err: _text_action(None))
_description = _text.copy()


_decimal = Word(nums).setParseAction(lambda t: int(t[0]))

_cmd_state = None

def _get_reset_cmd_state_action(cmd):
    def _reset_cmd_state_action(t):
        global _cmd_state
        if cmd is None or (_cmd_state is not None and _cmd_state == cmd):
            _cmd_state = None
    return Empty().setParseAction(_reset_cmd_state_action)

def _get_keyword_action(kw):
    def _keyword_action(s, l, t):
        if t[0].upper() != kw.upper():
            raise ParseException(s, l, "expected keyword")
        return kw
    return _keyword_action

def _keyword(kw):
    return _word.copy().setParseAction(_get_keyword_action(kw))

def _get_cmd_action(cmd):
    def _cmd_action(t):
        global _cmd_state
        if _cmd_state is None:
            _cmd_state = cmd
        return cmd
    return _cmd_action

def _command(name, real=None):
    cmd = _keyword(name) if name else Empty()
    return cmd.addParseAction(_get_cmd_action(real or name))

_start = StringStart()
_end = StringEnd()

def _bound_command(body):
    return _start + body + _end

def _command_string(body):
    cmd_str = _bound_command(body)
    if debug.enabled:
        cmd_str |= _bound_command(_command("T") + _decimal + _get_reset_cmd_state_action("T") + Group(body))
    return cmd_str

def _shortcut(s):
    return Empty().addParseAction(lambda t: s)


_show_db = _keyword("DB") | _keyword("DATABASES")
_show_strat = _keyword("STRAT") | _keyword("STRATEGIES")
_show_info = _keyword("INFO") + _word
_show_server = _keyword("SERVER") + Optional(_text)

_show_params = _show_db | _show_strat | _show_info | _show_server

_grammar = _command_string(_command("") + _get_reset_cmd_state_action(None))
_grammar |= _command_string(_command("DEFINE") + _word + _word) | _command_string(_command("D", "DEFINE") + _shortcut("*") + _word) | _command_string(_command("D", "DEFINE") + _word + _word)
_grammar |= _command_string(_command("MATCH") + _word + _word + _word) | _command_string(_command("M", "MATCH") + _shortcut("*") + _shortcut(".") + _word) | _command_string(_command("M", "MATCH") + _shortcut("*") + _word + _word) | _command_string(_command("M", "MATCH") + _word + _word + _word)
_grammar |= _command_string(_command("SHOW") + _show_params)
_grammar |= _command_string(_command("CLIENT") + Optional(_text, default=""))
_grammar |= _command_string(_command("STATUS") + Optional(_text)) | _command_string(_command("S", "STATUS") + Optional(_text))
_grammar |= _command_string(_command("HELP") + Optional(_text)) | _command_string(_command("H", "HELP") + Optional(_text))
_grammar |= _command_string(_command("QUIT") + Optional(_text)) | _command_string(_command("Q", "QUIT") + Optional(_text))
_grammar |= _command_string(_command("OPTION") + Optional(_text)) # not supported, therefore defined liberally
_grammar |= _command_string(_command("AUTH") + Optional(_text)) # not supported, therefore defined liberally
_grammar |= _command_string(_command("SASLAUTH") + Optional(_text)) # not supported, therefore defined liberally
_grammar |= _command_string(_command("SASLRESP") + Optional(_text)) # not supported, therefore defined liberally

_grammar.parseWithTabs()


_parser_lock = None


def parse_command(line):
    with _parser_lock:
        try:
            results = _grammar.parseString(line)
            logger.debug("parser results: %s", results)
            return True, results
        except ParseException as pe:
            logger.debug(pe)
            return False, _cmd_state

def init():
    global _parser_lock
    _parser_lock = modules.mp().Lock()
    global logger
    logger = logging.getLogger(__name__)
