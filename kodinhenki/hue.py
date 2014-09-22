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
# Last modified: Mon Sep 22 17:08:43 2014 mstenber
# Edit time:     31 min
#
"""

phue <> kodinhenki integration

Basic idea:
- poll all lights
- populate objects in the database based on that

"""

MAIN_NAME='hue'
BULB_NAME='%s.%s'

from kodinhenki.db import Object
import phue

class HueBulb(Object):
    _on_dirty = False
    def get_light_object(self):
        db = self.get_database()
        hue = get(db)
        light_name = self.get('light_name')
        for light in hue.b.get_light_objects():
            if light.name == light_name:
                return light
        raise KeyError(light_name)
    def is_on(self):
        if self._on_dirty:
            db = self.get_database()
            hue = get(db)
            hue.update()
            self._on_dirty = False
        return self.get('on')
    def turn_on(self):
        if self.is_on():
            return
        lo = self.get_light_object()
        lo.on = True
        self._on_dirty = True
    def turn_off(self):
        if not self.is_on():
            return
        lo = self.get_light_object()
        lo.on = False
        self._on_dirty = True


class Hue(Object):
    # Lights are stored not as objects, but as names
    def get_lights(self):
        return self.get_defaulted('lights', [])
    def get_light_objects(self):
        return [self.get_database().get(x) for x in self.get_lights()]
    def init(self, ip):
        self.b = phue.Bridge(ip)
    def update(self):
        db = self.get_database()
        l = []
        for light in self.b.get_light_objects():
            #name = unicode(light.name, 'utf-8')
            name = light.name
            n = BULB_NAME % (MAIN_NAME, name)
            if not db.exists(n):
                b = HueBulb(name=n, light_name=name)
                db.add_object(b)
            else:
                b = db.get(n)
            b.set('on', light.on)
            l.append(n)
        l.sort()
        self.set('lights', l)


def get(db):
    if not db.exists(MAIN_NAME):
        hue = Hue(name=MAIN_NAME)
        db.add_object(hue)
        return hue
    return db.get(MAIN_NAME)
