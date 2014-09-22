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
# Last modified: Mon Sep 22 20:09:08 2014 mstenber
# Edit time:     73 min
#
"""

phue <> kodinhenki integration

Basic idea:
- poll all lights
- populate objects in the database based on that

"""

MAIN_NAME='hue'
BULB_NAME='%s.%s'

import kodinhenki.db
import phue
import time
import threading

def _timestamp():
    return time.time()

class HueBulb(kodinhenki.db.Object):
    def get_parent(self):
        db = self.get_database()
        return get(db)
    def get_bridge(self):
        return self.get_parent().get_bridge()
    def get_light_object(self):
        # No explicit locking here, but expected caller to make sure
        # bridge isn't accessed willy-nilly..
        light_name = self.get('light_name')
        for light in self.get_bridge().get_light_objects():
            if light.name == light_name:
                return light
        raise KeyError(light_name)
    def is_on(self):
        return self.get('on')
    def turn_on(self):
        self.set('on', True)
    def turn_off(self):
        self.set('on', False)

class Hue(kodinhenki.db.Object):
    # How long do we believe in the 'current' timestamp?
    # (in seconds)
    light_check_interval = 60

    # Update set of available lights dynamically (if not,
    # no need to re-create bridge object every now and then)
    dynamically_update_lights = False

    _lights_dirty_after = 0
    _b = None

    # per-CLASS lock - but who cares, there should be only one instance
    _lock = threading.RLock()

    def get_bridge(self, force=False):
        with self._lock:
            if not self._b or force:
                self._b = phue.Bridge(self.get('ip'))
            return self._b
    # Lights are stored not as objects, but as names
    def get_lights(self):
        return self.get_defaulted('lights', [])
    def get_light_objects(self):
        return [self.get_database().get(x) for x in self.get_lights()]
    def mark_dirty(self):
        self._lights_dirty_after = 0
    def is_dirty(self):
        if not self._lights_dirty_after:
            return True
        return self._lights_dirty_after <= _timestamp()
    def update(self):
        with self._lock:
            b = self.get_bridge(force=self.dynamically_update_lights)
            lobs = b.get_light_objects()
        db = self.get_database()
        with db._lock:
            l = []
            for light in lobs:
                #name = unicode(light.name, 'utf-8')
                name = light.name
                n = BULB_NAME % (MAIN_NAME, name)
                if not db.exists(n):
                    b = HueBulb(name=n, light_name=name)
                    db.add_object(b)
                else:
                    b = db.get(n)
                b.set('on', light.on, by='bridge')
                l.append(n)
            l.sort()
            self.set('lights', l, by='bridge')
        self._lights_dirty_after = _timestamp() + self.light_check_interval

def _bulb_changed(o, key, by, old, new):
    if key == 'on' and by != 'bridge' and o.name.startswith(MAIN_NAME):
        with o.get_database()._lock:
            hue = o.get_parent()
            with hue._lock:
                lo = o.get_light_object()
                lo.on = new
                hue.mark_dirty()

kodinhenki.db.Object.changed.connect(_bulb_changed)

get = kodinhenki.db.singleton_object_factory(MAIN_NAME, Hue)

