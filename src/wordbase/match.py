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


import string
import collections


_no_punctuation = {ord(c): None for c in string.punctuation}

def _preprocess(word):
    return ' '.join(word.translate(_no_punctuation).split()).lower()

def _match_exact(word, sample):
    return word == sample

def _match_prefix(word, sample):
    return sample.startswith(word)

_strategies = collections.OrderedDict((
                                       ("exact", ("Match headwords exactly", _match_exact)),
                                       ("prefix", ("Match prefixes", _match_prefix)),
                                     ))

_default_strategy = "prefix"


def get_strategy(name=None):
    def find_matches(word, samples):
        def test_sample(sample):
            return test(word, _preprocess(sample))
        word = _preprocess(word)
        matches = filter(test_sample, samples)
        return list(matches)

    if name is None:
        name = _default_strategy

    strat = _strategies.get(name)
    if strat is None:
        return None
    desc, test = strat
    del desc

    return find_matches

def get_strategies():
    func = None
    func = func
    strats = collections.OrderedDict([(name, desc) for name, (desc, func) in _strategies.items()])
    return strats

def configure(config):
    strategies = config.get("strategies", "")
    if strategies:
        parts = strategies.split(':')
        default, strats = parts

        global _strategies, _default_strategy
        user_strats = collections.OrderedDict()
        for strat in strats.split(','):
            name = strat.strip()
            if name:
                if name not in _strategies:
                    raise ValueError("unsupported strategy: {}".format(name))
                user_strats[name] = _strategies[name]
        _strategies = user_strats

        default = default.strip()
        if default not in _strategies:
            raise ValueError("default strategy not in list of advertised strategies")
        _default_strategy = default
