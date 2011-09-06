#/usr/bin/env python3

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
import os
import getopt
import configparser


PROGRAM_NAME = "wordbase"


_usage_help = \
"""usage: {name} [-d] [conf_file]

options:
 -d    daemon mode

arguments:
 conf  path to configuration file"""


def get_default_conf_path():
    conf_filename = PROGRAM_NAME + ".conf"
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    default_conf_path = os.path.join(script_dir, conf_filename)
    return default_conf_path

def usage():
    print(_usage_help.format(name=PROGRAM_NAME), file=sys.stderr)

def main():
    daemon = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-d":
            daemon = True
        else:
            assert False, "unhandled option"

    if len(args) == 1:
        conf_path = args[0]
    elif len(args) == 0:
        conf_path = get_default_conf_path()
    else:
        usage()
        sys.exit(2)

    with open(conf_path) as conf:
        config = configparser.ConfigParser()
        config.read_file(conf, conf_path)

    if daemon:
        raise NotImplementedError("daemon mode is not implemented")


try:
    main()
except Exception as ex:
    print(ex, file=sys.stderr)
    sys.exit(1)
