#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: user_active.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Wed Oct  1 15:25:26 2014 mstenber
# Last modified: Thu Nov  6 18:22:43 2014 mstenber
# Edit time:     26 min
#
"""

Simple user activity tracking

TBD: could do this for e.g. UNIX ttys or whatever, but OS X is enough
for me for now.

"""

import prdb
import kodinhenki.prdb_kh as _prdb_kh

import subprocess
import threading
import os


import logging
logger = logging.getLogger('kh.user_active')
_debug = logger.debug
_error = logger.error

def _start_reader_thread(command, callback, autostart=False):
    """ Start a process in a new thread which reads lines from the command,
    and calls callback for each line. """
    state = [True]
    def _reader():
        while state[0]:
            p = subprocess.Popen(command,
                                 stdout=subprocess.PIPE, bufsize=1, close_fds=True)
            for line in p.stdout:
                line = line.decode().strip()
                #_debug('got %s', line)
                callback(line)
            if autostart:
                _error('popen died - restarting')
                time.sleep(1)
            else:
                _error('popen died')
                return
    t = threading.Thread(target=_reader)
    t.daemon = True
    t.start()
    return (state, t)

user_active_period = 5 # in seconds

sleepwatcher = '/usr/local/sbin/sleepwatcher'

class UserActivityMonitor(prdb.Owner):
    _thread = None
    def init(self):
        pass
    def handle_state(self, state):
        if state == '0':
            self.o.set('on', False)
        elif state == '1':
            self.o.set('on', True)
        else:
            raise NotImplementedError("weird state:%s" % state)
    def start(self):
        t = str(user_active_period * 10) # sleepwatcher wants 10ths of second
        self._thread = _start_reader_thread([sleepwatcher, '-t', t,
                                             '-i', 'echo 0',
                                             '-R', 'echo 1'],
                                            self.handle_state)
    def stop(self):
        if not self._thread: return
        self._thread[0][0] = False
        os.system('killall -9 sleepwatcher')
        # Other subprocesses will restart sleepwatcher, eventually..
    def __del__(self):
        # TBD - how to get rid of the subprocess in self._thread
        self.stop()

_prdb_kh.UserActive.set_create_owner_instance_callback(UserActivityMonitor)

def start(name, db=None):
    _debug('starting user_active %s', name)
    now_idle = int(os.popen(sleepwatcher + ' -g').read()) / 10.0
    state = now_idle <= user_active_period and True or False
    o = _prdb_kh.UserActive.new_named(name, on=state).get_owner()
    o.start()
    return o

