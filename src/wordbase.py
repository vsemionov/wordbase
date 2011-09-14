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
import logging
import random

import log
import daemon


PROGRAM_NAME = "wordbase"
PROGRAM_VERSION = "0.1"


logger = None

debug_mode = False

version_info = \
"""{name} {version}
Copyright (C) 2011 Victor Semionov"""

usage_help = \
"""Usage: {name} [-f conf_file] [-d command] [-D]

Options:
 -v            print version information and exit
 -h            print this help message and exit
 -f conf_file  read the specified configuration file
 -d            daemon mode
 -D            debug mode

Daemon control commands:
 start         start daemon
 stop          stop daemon
 restart       restart daemon"""

help_hint = "Try '{name} -h' for more information."


class WBDaemon(daemon.Daemon):
    def __init__(self, name, pidfile, task, *args):
        super().__init__(name, pidfile)
        self.run_task = task
        self.run_args = args

    def run(self):
        self.run_task(*self.run_args)


def get_default_conf_path():
    return "/etc/" + PROGRAM_NAME + ".conf"

def print_usage():
    print(usage_help.format(name=PROGRAM_NAME))

def print_version():
    print(version_info.format(name=PROGRAM_NAME, version=PROGRAM_VERSION))

def print_help_hint():
    print(help_hint.format(name=PROGRAM_NAME), file=sys.stderr)

def drop_privs(wbconfig):
    user = wbconfig["user"]
    group = wbconfig["group"]

    try:
        import pwd, grp
    except ImportError:
        return

    uentry = pwd.getpwnam(user)
    uid = uentry[2]
    gid = grp.getgrnam(group)[2] if group else uentry[3]

    try:
        os.setgid(gid)
        os.setuid(uid)
    except AttributeError:
        return

def start_server(wbconfig, mp):
    import master

    host = wbconfig["host"]
    port = int(wbconfig["port"])
    backlog = int(wbconfig["backlog"])
    timeout = int(wbconfig["timeout"])
    address = (host, port)

    master.init(address, backlog)
    drop_privs(wbconfig)
    master.run(timeout, mp)

def server_control(config, daemon_cmd):
    import modules

    start_cmd = "start"
    stop_cmd = "stop"
    restart_cmd = "restart"

    wbconfig = config["wordbase"]

    pidfile = wbconfig["pidfile"]
    wbdaemon = WBDaemon(PROGRAM_NAME, pidfile, start_server)
    control_func = None

    if daemon_cmd in (None, start_cmd, restart_cmd):
        random.seed()

        modules.init(config)

        import match
        import core

        print(config)
        dconfig = config["dict"]
        match.configure(dconfig["strategies"])
        core.configure(dconfig["server"], dconfig["domain"])

        wbdaemon.run_args = (wbconfig, modules.mp())

        if daemon_cmd == start_cmd:
            control_func = wbdaemon.start
        elif daemon_cmd == restart_cmd:
            control_func = wbdaemon.restart
        elif daemon_cmd is None:
            control_func = wbdaemon.run
        else:
            assert False, "unhandled command"

        log_init = True
    elif daemon_cmd == stop_cmd:
        control_func = wbdaemon.stop
        log_init = False
    else:
        print("command \"{}\" not recognized".format(daemon_cmd), file=sys.stderr)
        print_help_hint()
        sys.exit(2)

    if log_init:
        logger.debug("initialized")

    control_func()

def main():
    conf_path = None
    daemon = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhf:d:D")
    except getopt.GetoptError as ge:
        print(ge, file=sys.stderr)
        print_help_hint()
        sys.exit(2)

    if len(args):
        print("excess argument(s)", file=sys.stderr)
        print_help_hint()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-v":
            print_version()
            return
        elif opt == "-h":
            print_usage()
            return
        elif opt == "-f":
            conf_path = arg
        elif opt == "-d":
            daemon = arg
        elif opt == "-D":
            global debug_mode
            debug_mode = True
        else:
            assert False, "unhandled option"

    if conf_path is None:
        conf_path = get_default_conf_path()

    log.configure(conf_path)

    global logger
    logger = logging.getLogger(PROGRAM_NAME)

    with open(conf_path) as conf:
        config = configparser.ConfigParser(inline_comment_prefixes="#")
        config.read_file(conf, conf_path)

    server_control(config, daemon)


try:
    main()
except KeyboardInterrupt:
    pass
except Exception as ex:
    err_msg = "{}: {}".format(ex.__class__.__name__, ex)
    log_msg = "terminating on unhandled exception"
    if logger:
        logger.critical(log_msg, exc_info=sys.exc_info())
        print(err_msg, file=sys.stderr)
    elif debug_mode:
        logging.critical(log_msg, exc_info=sys.exc_info())
    else:
        print(err_msg, file=sys.stderr)
    sys.exit(1)
