#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: bh1750fvi_light.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2015 Markus Stenberg
#
# Created:       Mon Aug 24 10:19:58 2015 mstenber
# Last modified: Mon Aug 24 11:12:30 2015 mstenber
# Edit time:     12 min
#
"""

This is i2c-based light sensor handler for BH1750FVI sensor.

The basic idea is that (to minimize unneccessary state churn) it will
only report changes that are 'significant', to prevent sensor noise
from showing up if it happens to be on edge of values.

"""

INTERESTING_DELTA=2
POLL_INTERVAL=2

import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.updater as _updater

import smbus

import logging
logger = logging.getLogger(__name__)
_debug = logger.debug
_error = logger.error

class LightSensor(_prdb_kh.LockedUpdated):
    update_interval = POLL_INTERVAL
    smbus_number = 1
    i2c_address = 0x23
    def __init__(self, name, **kw):
        self.__dict__.update(**kw)
        self.o = _prdb_kh.LightSensor.new_named(name, value=None)
        self.smbus = smbus.SMBus(self.smbus_number)
    def locked_next_update_in_seconds(self):
        return self.update_interval
    def locked_update(self):
        data = self.smbus.read_i2c_block_data(self.i2c_address, 0x11)
        lx = int((data[1] + (256 * data[0])) / 1.2)
        if self.o.value is not None and \
           abs(lx-self.o.value) < INTERESTING_DELTA: return
        self.o.value=lx

def start(name, **kw):
    u = LightSensor(name, **kw)
    _updater.add(u)
    return u


if __name__ == '__main__':
    import kodinhenki
    kodinhenki.get_database()
    ls = LightSensor('foo')
    ls.locked_update()
    print(ls.o.value)

