#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: hue.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 15:59:59 2014 mstenber
# Last modified: Mon Oct 27 22:32:02 2014 mstenber
# Edit time:     143 min
#
"""

phue <> kodinhenki integration

Basic idea:
- poll all lights
- populate objects in the database based on that

"""

MAIN_NAME='hue'
BULB_NAME='%s.%s'

import prdb
import kodinhenki
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.updater as updater
import phue
import time

BY_US='hue'

import logging
_debug = logging.debug
_error = logging.error

class HueBulb(prdb.Owner):
    def object_changed(self, **kwargs):
        get_updater().bulb_changed(self, **kwargs)
    def is_on(self):
        return self.o.get('on')
    def turn_on(self):
        self.o.set('on', True)
    def turn_off(self):
        self.o.set('on', False)

_prdb_kh.HueBulb.set_create_owner_instance_callback(HueBulb)

class HueUpdater(prdb.Owner, updater.Updated):
    # How long do we believe in the 'current' timestamp?
    # (in seconds)
    light_check_interval = 30

    # Update set of available lights dynamically (if not,
    # no need to re-create bridge object every now and then)
    dynamically_update_lights = False

    _lights_dirty_after = 0
    _b = None

    def bulb_changed(self, b, key, new, by, **kwargs):
        _debug('bulb_changed %s %s %s %s' % (b, key, new, by))
        if not (key == 'on' and by != BY_US):
            return
        _debug('setting light state %s=%s' % (b.o.light_name, new))
        light_name = b.o.get('light_name')
        b = self.get_bridge(force=self.dynamically_update_lights)
        d = b.get_light_objects(mode='name')
        lo = d.get(light_name, None)
        if not lo:
            raise KeyError(light_name)
        lo.on = new
        self.mark_dirty()
    def get_bridge(self, force=False):
        if not self._b or force:
            self._b = phue.Bridge(self.o.get('ip'))
        return self._b
    def mark_dirty(self):
        self._lights_dirty_after = 0
        self.next_update_in_seconds_changed()
    # Updated implementation
    def next_update_in_seconds(self):
        return self._lights_dirty_after - time.time()
    def update(self):
        b = self.get_bridge(force=self.dynamically_update_lights)
        lobs = b.get_light_objects(mode='name')
        for name, light in lobs.items():
            is_on = light.on
            bulb = _prdb_kh.HueBulb.new_named(name, light_name=name, on=is_on).get_owner()
        self._lights_dirty_after = time.time() + self.light_check_interval
        # we're automatically readded post-update

_prdb_kh.HueUpdater.set_create_owner_instance_callback(HueUpdater)

def get_updater(**kwargs):
    return _prdb_kh.HueUpdater.new_named(**kwargs).get_owner()

# backwards compatible API
get = get_updater
