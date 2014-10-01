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
# Last modified: Wed Oct  1 15:38:52 2014 mstenber
# Edit time:     13 min
#
"""

Simple user activity tracking

TBD: could do this for e.g. UNIX ttys or whatever, but OS X is enough
for me for now.

"""

import kodinhenki.db

import subprocess
import threading
import os

def _start_reader_thread(command, callback, autostart=False):
    """ Start a process in a new thread which reads lines from the command,
    and calls callback for each line. """
    def _reader():
        while 1:
            p = subprocess.Popen(command,
                                 stdout=subprocess.PIPE, bufsize=1, close_fds=True)
            for line in p.stdout:
                line = line.decode().strip()
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
    return t

class UserActivityMonitor(kodinhenki.db.Object):
    user_active_period = 5 # in seconds
    sleepwatcher = '/usr/local/sbin/sleepwatcher'
    def __init__(self, *args, **kwargs):
        # Determine initial state by hand
        if 'on' not in kwargs:
            now_idle = int(os.popen(self.sleepwatcher + ' -g').read()) / 10.0
            state = now_idle <= self.user_active_period and True or False
            kwargs['on'] = state
        kodinhenki.db.Object.__init__(self, *args, **kwargs)
        t = str(self.user_active_period * 10) # sleepwatcher wants 10ths of second
        def _handle_state(state):
            if state == '0':
                self.set('on', False)
            elif state == '1':
                self.set('on', True)
            else:
                raise NotImplementedError("weird state:%s" % state)
        self._thread = _start_reader_thread([self.sleepwatcher, '-t', t,
                                             '-i', 'echo "0"',
                                             '-R', 'echo "1"'],
                                            _handle_state)
    def __del__(self):
        # TBD - how to get rid of the subprocess in self._thread
        pass

def start(name, db=None):
    db = db or kodinhenki.db.get_database()
    return db.add_object(UserActivityMonitor(name))

