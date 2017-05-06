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
# Last modified: Fri May  5 14:37:35 2017 mstenber
# Edit time:     246 min
#
"""

phue <> kodinhenki integration

Basic idea:
- poll all lights
- populate objects in the database based on that

"""

import calendar
import datetime
import logging
import time

import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.updater as _updater
import phue

import prdb

BY_US = 'hue'

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


class RepeatingTimer:

    def __init__(self, interval):
        self.interval = interval
        self.force()

    def force(self):
        self.t = 0

    def if_expired_reset(self):
        if self.is_expired():
            self.reset()
            return True

    def is_expired(self):
        return not (self.time_left() > 0)

    def reset(self):
        self.t = time.time()

    def time_left(self):
        return max(0, (self.t + self.interval) - time.time())

tap_event2key = {34: 'off',
                 16: '2',
                 17: '3',
                 18: '4'}


class HueUpdater(prdb.Owner, _updater.Updated):
    # How often do we want to poll the sensors?
    # (in seconds)
    check_timer = RepeatingTimer(3)

    # Update set of available lights dynamically (if not,
    # no need to re-create bridge object every now and then)
    dynamically_update_lights = False

    _b = None
    _motion_sensors = []
    _taps = []

    def bulb_changed(self, b, key, new, by, **kwargs):
        _debug('bulb_changed %s %s %s %s', b, key, new, by)
        if not (key == 'on' and by != BY_US):
            return
        _debug('setting light state %s=%s', b.light_name, new)
        bridge = self.get_bridge(force=self.dynamically_update_lights)
        d = bridge.get_light_objects(mode='name')
        lo = d.get(b.light_name, None)
        if not lo:
            raise KeyError(b.light_name)
        lo.on = new
        self.mark_dirty()

    def get_bridge(self, force=False):
        if not self._b or force:
            with _prdb_kh.lock:
                self._b = phue.Bridge(self.ip)
        return self._b

    def mark_dirty(self):
        self.check_timer.force()
        self.next_update_in_seconds_changed()

    def next_update_in_seconds(self):
        return self.check_timer.time_left()

    def update(self):
        b = self.get_bridge(force=self.dynamically_update_lights)
        self.check_timer.reset()
        lights = b.get_light()
        for _, o in lights.items():
            name = o['name']
            is_on = o['state']['on']
            with _prdb_kh.lock:
                o = _prdb_kh.HueBulb.new_named(name, on=is_on).get_owner()
                o.light_name = name

        # Convert it to get_sensor_objects style output
        sensors = b.get_sensor()
        sensors = [(int(k), v) for k, v in sensors.items()]
        sensors.sort()

        # Philips Motion sensors are funny beasts; they have:
        #
        # N-1 = Hue temperature sensor ..
        # N = actual sensor (battery, presence)
        # N + 1 = Hue ambient light sensor ..
        # N + 2 = MotionSensor
        #
        # (additional -1 in the accesses due to Python list index
        # starting at 0, not 1)

        for i, (_, o) in enumerate(sensors, 1):
            name = o['name']
            st = o['state']
            presence = st.get('presence')
            if presence is not None:
                with _prdb_kh.lock:
                    _prdb_kh.HueMotion.new_named(name, on=presence)
                    # b = v.get_owner()
                    # b.light_name = name
            elif name.startswith('Hue temperature sensor'):
                name = sensors[i + 1 - 1][1]['name']
                value = '%.1f' % round(st['temperature'] / 100.0, 1)
                with _prdb_kh.lock:
                    _prdb_kh.HueTemperature.new_named(name, value=value)
            elif name.startswith('Hue ambient light sensor'):
                name = sensors[i - 1 - 1][1]['name']
                value = int(10 ** (st['lightlevel'] / 10000.0))
                with _prdb_kh.lock:
                    _prdb_kh.HueLight.new_named(name, value=value)
            elif name.lower().find('tap') >= 0:
                event = st.get('buttonevent')
                lu = st.get('lastupdated')
                if event and lu:
                    key = tap_event2key[event]
                    fname = '%s.%s' % (name, key)
                    # Parse the ISO8601 timestamp, assume UTC
                    dt = datetime.datetime.strptime(
                        lu, "%Y-%m-%dT%H:%M:%S")
                    with _prdb_kh.lock:
                        o = _prdb_kh.HueTap.new_named(fname)
                        t = calendar.timegm(dt.timetuple())
                        o.set('on', False, when=t)

_prdb_kh.HueUpdater.set_create_owner_instance_callback(HueUpdater)


def get_updater(ip=None, **kwargs):
    o = _prdb_kh.HueUpdater.new_named(**kwargs).get_owner()
    if ip:
        o.ip = ip
    return o

# backwards compatible API
get = get_updater
