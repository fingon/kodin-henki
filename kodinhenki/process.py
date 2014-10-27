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
# Last modified: Mon Oct 27 21:28:04 2014 mstenber
# Edit time:     16 min
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
logger = logging.getLogger('kh.user_active')
_debug = logger.debug
_error = logger.error

PS_STRING = 'ps awx'

class ProcessMonitor(updater.Updated):
    def __init__(self, pdict):
        self.pdict = pdict
        # Add the objects
        for name in pdict.keys():
            _prdb_kh.Process.new_named(name, on=False)
    def next_update_in_seconds(self):
        return 30 # hardcoded, but oh well
    def update(self):
        with os.popen(PS_STRING, 'r') as psfile:
            lines = list(psfile)
        # We _know_ the objects exist
        for name, match in self.pdict.items():
            on = True if any (match in l for l in lines) else False
            _prdb_kh.Process.get_named(name).on=on

def start(d):
    _debug('starting process %s', repr(d))
    m = ProcessMonitor(d)
    updater.add(m)
    return m
