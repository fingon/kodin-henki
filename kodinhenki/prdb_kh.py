#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: prdb_kh.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Oct 27 18:00:17 2014 mstenber
# Last modified: Wed Jan 21 17:54:38 2015 mstenber
# Edit time:     40 min
#
"""

Kodinhenki schema declaration for prdb

"""

import prdb
import threading
import types
import kodinhenki.updater as _updater
import logging

_logger = logging.getLogger('kh.prdb')
_debug = _logger.debug

KH = prdb.App('kh', version=1)

HueBulb = KH.declare_class('hue')

HueUpdater = KH.declare_class('hue_updater')

WemoTracker = KH.declare_class('wemo_tracker')

WemoSwitch = KH.declare_class('wemo_switch')
WemoMotion = KH.declare_class('wemo_motion')

Process = KH.declare_class('process')

Home = KH.declare_class('home')

UserActive = KH.declare_class('user_active')

WifiDevice = KH.declare_class('wifi')

import inspect

class LogLock(object):
    def __init__(self, cl):
        self.lock = cl()
    def _acquire(self, stack, who, *a, **kw):
        if self.lock.acquire(blocking=False, *a, **kw):
            _debug('%s %s (got)', stack, who)
            return True
        _debug('%s %s (pending)', stack, who)
        return self.lock.acquire(*a, **kw)
    def acquire(self, *a, **kw):
        return self._acquire(inspect.stack()[1], *a, **kw)
    def release(self):
        _debug('%s release', inspect.stack()[1])
        self.lock.release()
    def _is_owned(self):
        return self.lock._is_owned()
    def __enter__(self):
        return self._acquire(inspect.stack()[1], 'enter')
    def __exit__(self, *args):
        _debug('%s exit', inspect.stack()[1])
        self.lock.release()
        return False

#lock = threading.RLock()
lock = LogLock(threading.RLock)

# Debug code to make sure lock IS used whenever accessing Object/Database
import prdb.db as _db

_enable_lock_check = False

def _instrument_class_method_check_lock(cl, k):
    v = getattr(cl, k)
    if type(v) != types.FunctionType:
        return
    def _f(*args, **kwargs):
        assert not _enable_lock_check or lock._is_owned()
        return v(*args, **kwargs)
    setattr(cl, k, _f)


def _instrument_class_check_lock(cl, recurse=False):
    for k in cl.__dict__.copy().keys():
        _instrument_class_method_check_lock(cl, k)
    if recurse:
        _instrument_class_check_lock(super(cl), recurse)

_instrument_class_check_lock(_db.Database)
_instrument_class_check_lock(_db.Object)

def set_lock_check_enabled(x):
    global _enable_lock_check
    old = _enable_lock_check
    _enable_lock_check = x
    return old

class LockedUpdated(_updater.Updated):
    def update(self, *args, **kwargs):
        with lock:
            return self.locked_update(*args, **kwargs)
    def next_update_in_seconds(self):
        with lock:
            return self.locked_next_update_in_seconds()
    def locked_next_update_in_seconds(self):
        raise NotImplementedError
    def locked_update(self):
        raise NotImplementedError
