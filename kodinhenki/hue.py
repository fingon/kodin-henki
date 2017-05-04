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
# Last modified: Thu Apr 27 23:46:52 2017 mstenber
# Edit time:     224 min
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
    # How long do we believe in the 'current' timestamp?
    # (in seconds)
    light_check_timer = RepeatingTimer(10)

    temperature_timer = RepeatingTimer(300)  # won't get updated more often
    ambient_light_timer = RepeatingTimer(300)  # TBD
    motion_timer = RepeatingTimer(3)  # as often as possible

    tap_timer = RepeatingTimer(10)

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
        self.light_check_timer.force()
        self.next_update_in_seconds_changed()

    def next_update_in_seconds(self):
        return min(self.light_check_timer.time_left(),
                   self.motion_timer.time_left())

    def update(self):
        b = self.get_bridge(force=self.dynamically_update_lights)
        if self.light_check_timer.if_expired_reset():
            lobs = b.get_light_objects(mode='name')
            for name, light in lobs.items():
                is_on = light.on
                with _prdb_kh.lock:
                    o = _prdb_kh.HueBulb.new_named(name, on=is_on).get_owner()
                    o.light_name = name

        # Philips Motion sensors are funny beasts; they
        # have at index N one with e.g. battery, presence.
        #
        # N-1 = Hue temperature sensor ..
        # N + 1 = Hue ambient light sensor ..
        # N + 2 = MotionSensor
        #
        # (additional -1 in the accesses due to Python list index
        # starting at 0, not 1)

        sensors = None
        if self.temperature_timer.if_expired_reset():
            sensors = sensors or b.get_sensor_objects()
            for i, o in enumerate(sensors, 1):
                if o.name.startswith('Hue temperature sensor'):
                    name = sensors[i + 1 - 1].name
                    value = '%.1f' % round(o.state['temperature'] / 100.0, 1)
                    # TBD: Does this need better smoothing?
                    with _prdb_kh.lock:
                        _prdb_kh.HueTemperature.new_named(name, value=value)

        if self.ambient_light_timer.if_expired_reset():
            sensors = sensors or b.get_sensor_objects()
            for i, o in enumerate(sensors, 1):
                if o.name.startswith('Hue ambient light sensor'):
                    name = sensors[i - 1 - 1].name
                    value = int(10 ** (o.state['lightlevel'] / 10000.0))
                    with _prdb_kh.lock:
                        _prdb_kh.HueLight.new_named(name, value=value)

        if self.motion_timer.if_expired_reset():
            msensors = sensors or self._motion_sensors
            motion_sensors = []
            self._motion_sensors = motion_sensors
            for o in msensors:
                if o.name.endswith('M'):
                    name = o.name
                    presence = o.state.get('presence')
                    if presence is None:
                        continue
                    motion_sensors.append(o)
                    with _prdb_kh.lock:
                        _prdb_kh.HueMotion.new_named(name, on=presence)
                        # b = v.get_owner()
                        # b.light_name = name

        if self.tap_timer.if_expired_reset():
            tsensors = sensors or self._taps
            taps = []
            self._taps = taps
            for sensor in tsensors:
                name = sensor.name
                if name.lower().find('tap') >= 0:
                    st = sensor.state
                    event = st.get('buttonevent')
                    lu = st.get('lastupdated')
                    if event and lu:
                        taps.append(sensor)
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
