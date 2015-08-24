#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: process.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Wed Oct  1 15:10:38 2014 mstenber
# Last modified: Mon Aug 24 10:24:24 2015 mstenber
# Edit time:     18 min
#
"""

Simple process monitor.

Usage: .start({key: substring[, key: substring, ..]})

"""

import kodinhenki as kh
import kodinhenki.updater as updater
import kodinhenki.prdb_kh as _prdb_kh

import os
import logging

logger = logging.getLogger(__name__)
_debug = logger.debug
_error = logger.error

PS_STRING = 'ps awwx'

class ProcessMonitor(updater.Updated):
    update_interval = 30
    def __init__(self, pdict, **kw):
        self.pdict = pdict
        self.__dict__.update(**kw)
        # Add the objects
        for name in pdict.keys():
            _prdb_kh.Process.new_named(name, on=False)
    def next_update_in_seconds(self):
        return self.update_interval
    def update(self):
        with os.popen(PS_STRING, 'r') as psfile:
            self.update_lines(list(psfile))
    def update_lines(self, lines):
        # We _know_ the objects exist
        with _prdb_kh.lock:
            for name, match in self.pdict.items():
                on = True if any (match in l for l in lines) else False
                _prdb_kh.Process.get_named(name).on=on

def start(d, **kw):
    _debug('starting process %s', repr(d))
    m = ProcessMonitor(d, **kw)
    updater.add(m)
    return m
