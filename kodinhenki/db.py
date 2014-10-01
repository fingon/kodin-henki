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
# Last modified: Wed Oct  1 15:39:07 2014 mstenber
# Edit time:     86 min
#
"""

(Named, eventful object) database.

Note: This is intentionally very singlethreaded design, despite being
usable in multithreaded app too. In multithreaded app, some sort of
message queue abstraction should be used (e.g. pipe all signals
somewhere safe). The overhead of adding spurious locking also for
singlethreaded case does not seem very useful.

Due to GIL, there should not be THAT much need for locking of state in
any case. Nothing here should block (although who knows what
constructors called in singleton_object_factory do).

"""

import time
import kodinhenki.util

import logging
_debug = logging.debug
_error = logging.error


class Object:
    _db = None
    def __init__(self, name, **state):
        if state:
            now = time.time()
            state = dict([(key, (value, now, None)) for key, value in state.items()])
        self._state = state
        self.name = name
    def on_add_to_db(self, db):
        pass
    def on_remove_from_db(self, db):
        pass
    def set_db(self, db):
        if db:
            assert self._db is None
            self.on_add_to_db(db)
        else:
            assert self._db is not None
            self.on_remove_from_db(self._db)
        self._db = db
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
    def items(self):
        return self._state.items()
    def set(self, key, value, by=None, now=None):
        _debug('set %s.%s=%s %s' % (self.name, key, value, by))
        # Spurious set
        ost = self._state.get(key, None)
        if ost and ost[0] == value:
            _debug(' .. spurious, no change')
            return
        if not now:
            now = time.time()
        st = (value, now, by)
        self._state[key] = st
        ov = ost and ost[0]
        self._db.object_changed(o=self, key=key, old=ov, at=now, new=value, by=by)

class Database:
    def __init__(self):
        self._objects = {}
        self.object_added = kodinhenki.util.Signal()
        self.object_removed = kodinhenki.util.Signal()
        self.object_changed = kodinhenki.util.Signal()
    def add(self, name, by=None, **kwargs):
        return self.add_object(Object(name, **kwargs), by)
    def add_object(self, o, by=None):
        assert o.name not in self._objects
        self._objects[o.name] = o
        o.set_db(self)
        self.object_added(o=o, by=by)
        return o
    def exists(self, name):
        return name in self._objects
    def get(self, name):
        return self._objects[name]
    def items(self):
        return self._objects.items()
    def remove(self, name, by=None):
        self.remove_object(self.get(name), by)
    def remove_object(self, o, by=None):
        assert o.name in self._objects
        del self._objects[o.name]
        assert o._db is self
        o.set_db(None)
        self.object_removed(o=o, by=by)


def singleton_object_factory(name, cls):
    def _f(db, *args, **kwargs):
        if db.exists(name): return db.get(name)
        o = cls(name, *args, **kwargs)
        db.add_object(o)
        return o
    return _f

_db = None

def get_database():
    global _db
    if not _db: _db = Database()
    return _db

