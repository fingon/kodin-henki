#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: util.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 19:03:29 2014 mstenber
# Last modified: Mon Sep 22 19:04:19 2014 mstenber
# Edit time:     1 min
#
"""

"""

# Decoupled listener implementation with optional filtering
# (e.g. 'pysignal' is something like this, but Django semantics make
# it look much harder)

class Signal:
    def __init__(self):
        self._listeners = []
    def connect(self, callback, filter=None):
        self._listeners.append((callback, filter))
    def __call__(self, **kwargs):
        for fun, filter in self._listeners:
            if not filter or filter(kwargs):
                fun(**kwargs)
    def disconnect(self, callback, filter=None):
        self._listeners.remove((callback, filter))


