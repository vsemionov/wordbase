#!/usr/bin/env python3

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

import modules
import master


PROGRAM_NAME = "wordbase"
PROGRAM_VERSION = "0.1"


_version_info = \
"""{name} {version}
Copyright (C) 2011 Victor Semionov"""

_usage_help = \
"""usage: {name} [-d] [conf_file]

options:
 -d    daemon mode

arguments:
 conf  path to configuration file"""

_help_hint = "Try '{name} -h' for more information."


def get_default_conf_path():
    conf_filename = PROGRAM_NAME + ".conf"
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    default_conf_path = os.path.join(script_dir, conf_filename)
    return default_conf_path

def print_usage():
    print(_usage_help.format(name=PROGRAM_NAME))

def print_version():
    print(_version_info.format(name=PROGRAM_NAME, version=PROGRAM_VERSION))

def print_help_hint():
    print(_help_hint.format(name=PROGRAM_NAME), file=sys.stderr)

def start_server(address, backlog, timeout, daemon_mode):
    args = (address, backlog, timeout, modules.mp)
    if daemon_mode:
        import daemon
        with daemon.DaemonContext():
            master.run(*args)
    else:
        master.run(*args)

def main():
    daemon = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhv")
    except getopt.GetoptError as ge:
        print(ge, file=sys.stderr)
        print_help_hint()
        sys.exit(2)

    for opt, arg in opts:
        del arg
        if opt == "-d":
            daemon = True
        elif opt == "-h":
            print_usage()
            return
        elif opt == "-v":
            print_version()
            return
        else:
            assert False, "unhandled option"

    if len(args) == 1:
        conf_path = args[0]
    elif len(args) == 0:
        conf_path = get_default_conf_path()
    else:
        print("more than one argument specified", file=sys.stderr)
        print_help_hint()
        sys.exit(2)

    with open(conf_path) as conf:
        config = configparser.ConfigParser()
        config.read_file(conf, conf_path)

    modules.init(config)

    wbconfig = config["wordbase"]
    host = wbconfig["host"]
    port = int(wbconfig["port"])
    backlog = int(wbconfig["backlog"])
    timeout = int(wbconfig["timeout"])
    address = (host, port)
    start_server(address, backlog, timeout, daemon)


try:
    main()
except Exception as ex:
    print("{}: {}".format(ex.__class__.__name__, ex), file=sys.stderr)
    sys.exit(1)
