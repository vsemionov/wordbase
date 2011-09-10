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
import getopt
import configparser

import modules
import master
import daemon


PROGRAM_NAME = "wordbase"
PROGRAM_VERSION = "0.1"


debug_mode = False

version_info = \
"""{name} {version}
Copyright (C) 2011 Victor Semionov"""

usage_help = \
"""Usage: {name} [-f conf_file] [-p pidfile] [-d command] [-D]

Options:
 -v            print version information and exit
 -h            print this help message and exit
 -c conf_file  read the specified configuration file
 -p pidfile    use the specified process id file in deamon mode
 -d            daemon mode
 -D            debug mode

Daemon control commands:
 start         start daemon
 stop          stop daemon
 restart       restart daemon"""

help_hint = "Try '{name} -h' for more information."


class WBDaemon(daemon.Daemon):
    def __init__(self, name, pidfile, *args):
        super().__init__(name, pidfile)
        self.run_args = args

    def run(self):
        master.run(*self.run_args)


def get_default_conf_path():
    return "/etc/" + PROGRAM_NAME + ".conf"

def get_default_pidfile():
    return "/var/run/" + PROGRAM_NAME + ".pid"

def print_usage():
    print(usage_help.format(name=PROGRAM_NAME))

def print_version():
    print(version_info.format(name=PROGRAM_NAME, version=PROGRAM_VERSION))

def print_help_hint():
    print(help_hint.format(name=PROGRAM_NAME), file=sys.stderr)

def server_control(config, daemon_cmd, pidfile):
    start_cmd = "start"
    stop_cmd = "stop"
    restart_cmd = "restart"

    wbdaemon = WBDaemon(PROGRAM_NAME, pidfile)
    command_func = None

    if daemon_cmd in (None, start_cmd, restart_cmd):
        modules.init(config)

        wbconfig = config["wordbase"]
        host = wbconfig["host"]
        port = int(wbconfig["port"])
        backlog = int(wbconfig["backlog"])
        timeout = int(wbconfig["timeout"])
        address = (host, port)

        wbdaemon.run_args = (address, backlog, timeout, modules.mp)

        if daemon_cmd == start_cmd:
            command_func = wbdaemon.start
        elif daemon_cmd == restart_cmd:
            command_func = wbdaemon.restart
        elif daemon_cmd is None:
            command_func = wbdaemon.run
        else:
            assert False, "unhandled command"
    elif daemon_cmd == stop_cmd:
        command_func = wbdaemon.stop
    else:
        assert False, "unhandled command"

    command_func()

def main():
    conf_path = None
    pidfile = None
    daemon = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhc:p:d:D")
        del args
    except getopt.GetoptError as ge:
        print(ge, file=sys.stderr)
        print_help_hint()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-v":
            print_version()
            return
        elif opt == "-h":
            print_usage()
            return
        elif opt == "-c":
            conf_path = arg
        elif opt == "-p":
            pidfile = arg
        elif opt == "-d":
            daemon = arg
        elif opt == "-D":
            global debug_mode
            debug_mode = True
        else:
            assert False, "unhandled option"

    if conf_path is None:
        conf_path = get_default_conf_path()
    if pidfile is None:
        pidfile = get_default_pidfile()

    with open(conf_path) as conf:
        config = configparser.ConfigParser()
        config.read_file(conf, conf_path)

    server_control(config, daemon, pidfile)


try:
    main()
except Exception as ex:
    if not debug_mode:
        print("{}: {}".format(ex.__class__.__name__, ex), file=sys.stderr)
        sys.exit(1)
    else:
        raise
