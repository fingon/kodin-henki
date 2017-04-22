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
# Last modified: Sat Apr 22 14:20:22 2017 mstenber
# Edit time:     50 min
#
"""

Kodinhenki schema declaration for prdb

"""

import logging
import threading
import types

import prdb
# Debug code to make sure lock IS used whenever accessing Object/Database
import prdb.db as _db

from . import updater, util

_logger = logging.getLogger(__name__)
_debug = _logger.debug

KH = prdb.App('kh', version=1)

LightSensor = KH.declare_class('light_sensor')
MotionSensor = KH.declare_class('motion_sensor')

HueBulb = KH.declare_class('hue')

HueMotion = KH.declare_class('hue_motion')
HueLight = KH.declare_class('hue_light')
HueTemperature = KH.declare_class('hue_temperature')

HueUpdater = KH.declare_class('hue_updater')

WemoTracker = KH.declare_class('wemo_tracker')

WemoSwitch = KH.declare_class('wemo_switch')
WemoMotion = KH.declare_class('wemo_motion')

Process = KH.declare_class('process')

Home = KH.declare_class('home')

UserActive = KH.declare_class('user_active')

WifiDevice = KH.declare_class('wifi')

lock = util.create_rlock(assert_without=[updater._queue_lock])


_enable_lock_check = False
_instrumented_classes = False


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


def set_lock_check_enabled(x):
    global _enable_lock_check, _instrumented_classes
    if not _instrumented_classes:
        _instrument_class_check_lock(_db.Database)
        _instrument_class_check_lock(_db.Object)
        _instrumented_classes = True
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
