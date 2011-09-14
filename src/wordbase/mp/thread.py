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


import threading
import logging


max_threads = 0
guard_sem = None
start_evt = threading.Event()

logger = logging.getLogger(__name__)


Lock = threading.Lock


def configure(config):
    global max_threads, guard_sem
    max_threads = int(config["max-clients"])
    guard_sem = threading.Semaphore(max_threads)

    logger.debug("initialized")

def thread_task(task, sock, addr, *args):
    with guard_sem:
        start_evt.set()

        logger.debug("thread started")

        try:
            task(sock, addr, *args)
        except Exception:
            logger.exception("unhandled exception")
        finally:
            logger.debug("thread exiting")

def process(task, sock, addr, *args):
    if not guard_sem.acquire(False):
        logger.warning("max-clients limit exceeded; waiting for a thread to terminate")
        guard_sem.acquire()
    guard_sem.release()

    thr = threading.Thread(target=thread_task, args = (task, sock, addr) + args)
    thr.daemon = True
    thr.start()

    start_evt.wait()
    start_evt.clear()