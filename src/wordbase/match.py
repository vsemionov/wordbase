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
                                       ("exact", _match_exact),
                                       ("prefix", _match_prefix),
                                     ))

_default_strategy = "prefix"


def get_strategy(name=None):
    def find_matches(word, samples):
        word = _preprocess(word)
        def test_sample(sample):
            return test(word, _preprocess(sample))
        matches = filter(test_sample, samples)
        return matches
    if name is None:
        name = _default_strategy
    test = _strategies.get(name)
    return test and find_matches

def get_strategies():
    return _strategies.keys()

def configure(config):
    strats = config.get("strategies", "")
    if strats:
        global _strategies, _default_strategy
        user_strats = collections.OrderedDict()
        for idx, strat in enumerate(strats.split()):
            name = strat.strip()
            if name:
                if idx == 0:
                    _default_strategy = name
                user_strats[name] = _strategies[name]
        _strategies = user_strats
