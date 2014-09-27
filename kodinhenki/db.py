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
# Last modified: Sat Sep 27 18:45:25 2014 mstenber
# Edit time:     59 min
#
"""

(Named, eventful object) database.

Note: This is intentionally very singlethreaded design, despite being
usable in multithreaded app too. In multithreaded app, some sort of
message queue abstraction should be used (e.g. pipe all signals
somewhere safe). The overhead of adding spurious locking also for
singlethreaded case does not seem very useful.

"""

import datetime
import kodinhenki.compat as compat
queue = compat.get_queue()
import kodinhenki.util
import threading

class Object:
    added = kodinhenki.util.Signal()
    removed = kodinhenki.util.Signal()
    changed = kodinhenki.util.Signal()
    def __init__(self, name=None, **state):
        if state:
            now = datetime.datetime.now()
            state = dict([(key, (value, now)) for key, value in state.items()])
        self._state = state
        self.name = name
    def __del__(self):
        Object.removed(o=self)
    def get(self, key):
        return self._state[key][0]
    def get_defaulted(self, key, default=None):
        if key not in self._state:
            return default
        return self.get(key)
    def get_changed(self, key):
        return self._state[key][1]
    def get_database(self):
        return self._db
    def set(self, key, value, by=None):
        # Spurious set
        ost = self._state.get(key, None)
        if ost and ost[0] == value:
            return
        now = datetime.datetime.now()
        st = [value, now, by]
        self._state[key] = st
        ov = ost and ost[0]
        Object.changed(o=self, key=key, old=ov, new=value, by=by)

class Database:
    def __init__(self):
        self._objects = {}
        self._queue = queue.Queue()
        self._lock = threading.RLock()
    def add(self, name, **kwargs):
        o = Object(name=name, **kwargs)
        self.add_object(o)
    def add_object(self, o):
        assert o.name not in self._objects
        self._objects[o.name] = o
        o._db = self
        Object.added(o=o)
    def exists(self, name):
        return name in self._objects
    def get(self, name):
        return self._objects[name]
    def remove(self, name):
        self.remove_object(self.get(name))
    def remove_object(self, o):
        assert o.name in self._objects
        del self._objects[o.name]
        assert o._db is self
        del o._db
        Object.removed(o=o)


def singleton_object_factory(name, cls):
    def _f(db, *args, **kwargs):
        with db._lock:
            if db.exists(name): return db.get(name)
            o = cls(name=name, *args, **kwargs)
            db.add_object(o)
            return o
    return _f

_db = None

def get_database():
    global _db
    if not _db: _db = Database()
    return _db

