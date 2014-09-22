#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: db.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 14:35:55 2014 mstenber
# Last modified: Mon Sep 22 15:12:49 2014 mstenber
# Edit time:     14 min
#
"""

(Named, eventful object) database

"""

import datetime

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

class Object:
    added = Signal()
    removed = Signal()
    changed = Signal()
    def __init__(self, name=None, **state):
        self._state = state
        self._name = name
        Object.added(o=self)
        if name:
            self.set('name', name)
    def __del__(self):
        Object.removed(o=self)
    def get(self, key):
        return self._state[key][0]
    def get_changed(self, key):
        return self._state[key][1]
    def set(self, key, value):
        # Spurious set
        ost = self._state.get(key, None)
        if ost and ost[0] == value:
            return
        now = datetime.datetime.now()
        st = [value, now]
        self._state[key] = st
        ov = ost and ost[0]
        Object.changed(o=self, key=key, old=ov, new=value)

class Database:
    def __init__(self):
        self._objects = {}
    def add(self, name, **kwargs):
        assert name not in self._objects
        o = Object(name=name, **kwargs)
        self._objects[name] = o

_db = None

def getDatabase():
    global _db
    if not _db: _db = Database()
    return _db

