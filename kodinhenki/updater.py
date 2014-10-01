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
# Last modified: Wed Oct  1 12:52:57 2014 mstenber
# Edit time:     21 min
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
        with _queue_lock:
            if self in _queue:
                remove(self)
                add(self)
            # If we're not in queue, does not matter
    def next_update_in_seconds(self):
        raise NotImplementedError
    def update(self):
        raise NotImplementedError

_queue = {}
_queue_lock = threading.RLock()

def add(o):
    assert isinstance(o, Updated)
    nu = o.next_update_in_seconds()
    if nu < 0:
        nu = 0
    t = threading.Timer(nu, _run)
    def _run():
        with _queue_lock:
            # If the object somehow disappeared/changed in queue, do nothing
            if _queue.get(o, None) is not t:
                return
            remove(o)
        o.update()
        with _queue_lock:
            # Do not re-add object if it caused itself to be added..
            if o in _queue:
                return
            add(o)
    with _queue_lock:
        assert not o in _queue
        t.start()
        _queue[o] = t

def is_empty():
    return not len(_queue)

def remove(o):
    assert isinstance(o, Updated)
    with _queue_lock:
        assert o in _queue
        _queue[o].cancel()
        del _queue[o]

def remove_all():
    with _queue_lock:
        for o, t in _queue.items():
            remove(o)
