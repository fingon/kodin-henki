#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: updater.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Tue Sep 30 07:16:50 2014 mstenber
# Last modified: Tue Sep 30 07:37:27 2014 mstenber
# Edit time:     16 min
#
"""

This is ~lightweight magic mechanism which hides the details of
time-based updates and the associated multithreading (mostly) from
client applications.

The idea is that clients, who implement the Updated interface,
register themselves, and get called automatically _in their own worker
threads_ when they should.

Note that the assumption is that the 'updated' object set may change
dynamically, but the actual timeouts do not. If this is a problem, you
can remove+readd object.

"""

import threading

class Updated:
    def next_update_in_seconds_changed(self):
        with _lock:
            if self in _queue:
                remove(self)
                add(self)
    def next_update_in_seconds(self):
        raise NotImplementedError
    def update(self):
        raise NotImplementedError

_queue = {}
_lock = threading.RLock()

def add(o):
    assert isinstance(o, Updated)
    nu = o.next_update_in_seconds()
    if nu < 0:
        nu = 0
    t = threading.Timer(nu, _run)
    def _run():
        with _lock:
            # If the object somehow disappeared/changed in queue, do nothing
            if _queue.get(o, None) is not t:
                return
            remove(o)
        o.update()
        with _lock:
            # Do not re-add object if it caused itself to be added..
            if o in _queue:
                return
            add(o)
    with _lock:
        assert not o in _queue
        t.start()
        _queue[o] = t

def is_empty():
    return not len(_queue)

def remove(o):
    assert isinstance(o, Updated)
    with _lock:
        assert o in _queue
        _queue[o].cancel()
        del _queue[o]

def remove_all():
    with _lock:
        for o, t in _queue.items():
            remove(o)

