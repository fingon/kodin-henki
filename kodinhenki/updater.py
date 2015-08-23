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
# Last modified: Sun Aug 23 12:30:32 2015 mstenber
# Edit time:     58 min
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

from . import util

import threading

import logging
logger = logging.getLogger(__name__)
_debug = logger.debug
_error = logger.error

_queue = {}
_queue_lock = util.create_rlock()

class Updated:
    def next_update_in_seconds_changed(self):
        add(self, update=True)
    def next_update_in_seconds(self):
        raise NotImplementedError
    def update(self):
        raise NotImplementedError

def add(o, update=False):
    assert isinstance(o, Updated)
    def _run():
        with _queue_lock:
            # If the object somehow disappeared/changed in queue, do nothing
            if _queue.get(o, None) is not t:
                return
        try:
            o.update()
        finally:
            add(o, update=True)
    nu = o.next_update_in_seconds()
    with _queue_lock:
        if update:
            # If we want to re-add ourselves (update), but we are no
            # longer in queue, we simply punt and do not re-add
            # ourselves.
            if o not in _queue:
                return
            remove(o)
        if nu is None:
            return
        if nu <= 0:
            nu = 1
        t = threading.Timer(nu, _run)
        _debug('adding in %s:%s = %s', nu, _run, t)
        assert not o in _queue
        _queue[o] = t
    t.start()

def is_empty():
    return not len(_queue)

def remove(o):
    assert isinstance(o, Updated)
    with _queue_lock:
        assert o in _queue
        _debug('canceling %s', o)
        _queue[o].cancel()
        del _queue[o]

def remove_all():
    with _queue_lock:
        while not is_empty():
            for o, t in _queue.items():
                remove(o)
                break
