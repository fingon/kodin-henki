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
# Last modified: Sat Oct  4 14:46:48 2014 mstenber
# Edit time:     11 min
#
"""

Simple process monitor.

Usage: .start({key: substring[, key: substring, ..]})

"""

import kodinhenki as kh
import kodinhenki.updater as updater

import os

PS_STRING = 'ps awx'

class ProcessMonitor(updater.Updated):
    def __init__(self, db, pdict):
        self.db = db or kh.get_database()
        self.pdict = pdict
        # Add the objects
        for k in pdict.keys():
            self.db.get_or_create(name=k).set('on', False)
    def next_update_in_seconds(self):
        return 30 # hardcoded, but oh well
    def update(self):
        with os.popen(PS_STRING, 'r') as psfile:
            lines = list(psfile)
        # We _know_ the objects exist
        for name, match in self.pdict.items():
            on = True if any (match in l for l in lines) else False
            self.db.get(name).set('on', on)

def start(d, db=None):
    m = ProcessMonitor(db, d)
    updater.add(m)
    return m
