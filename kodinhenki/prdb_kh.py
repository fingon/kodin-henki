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
# Last modified: Mon Aug 24 10:49:03 2015 mstenber
# Edit time:     48 min
#
"""

Kodinhenki schema declaration for prdb

"""

from . import updater
from . import util

import prdb

import threading
import types

import logging
_logger = logging.getLogger(__name__)
_debug = _logger.debug

KH = prdb.App('kh', version=1)

LightSensor = KH.declare_class('light_sensor')
MotionSensor = KH.declare_class('motion_sensor')

HueBulb = KH.declare_class('hue')

HueUpdater = KH.declare_class('hue_updater')

WemoTracker = KH.declare_class('wemo_tracker')

WemoSwitch = KH.declare_class('wemo_switch')
WemoMotion = KH.declare_class('wemo_motion')

Process = KH.declare_class('process')

Home = KH.declare_class('home')

UserActive = KH.declare_class('user_active')

WifiDevice = KH.declare_class('wifi')

lock = util.create_rlock(assert_without=[updater._queue_lock])

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

class LockedUpdated(updater.Updated):
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
