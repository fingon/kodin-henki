#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: cer-start.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Created:       .. sometime ~spring 2014 ..
# Last modified: Sat Apr 22 16:34:14 2017 mstenber
# Edit time:     334 min
#
"""

My home customizations (don't use this at your home ;->)

The idea is to run this at CER (which is always on, and has Python
available). It is the main responsible party for dealing with actual
control of e.g. WeMo and Belkin devices.

The other ones (poro-, fubuki-) run on computers to mainly provide the
idle or non-idle state and potentially also manipulate their own state (such as screen blanking etc) based on what is going on.

"""

import datetime
import logging
import os
import socket
import time

import kodinhenki as kh
import kodinhenki.hue as hue
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.suncalc as suncalc
import kodinhenki.updater as updater
import kodinhenki.user_active as ua

import khserver
import poroserver
import prdb

logger = logging.getLogger(__name__)
_debug = logger.debug


# activity sources
IP = '.kh.user_active.poro'
LS = '.kh.hue_light.KitchenM'
PHONES = ['.kh.wifi.iphone']
MST = '.kh.hue_motion.BathroomM'
MSH = '.kh.hue_motion.HallwayM'
MSK = '.kh.hue_motion.KitchenM'

# lights to be controlled
LB = '.kh.hue.Bed'
LC = '.kh.hue.Entry'
LK = '.kh.hue.Kitchen'
LR = '.kh.hue.Living'
# WT='.kh.wemo_switch.switch2'
LT = '.kh.hue.Toilet'

# Which light do we care about when it's daylight?
DAYLIGHT_LIGHTS = [LT, LC]
# SENSOR_BUILT_IN_DELAY={IP: ua.user_active_period + 1} # now done in ua
SENSOR_BUILT_IN_DELAY = {}

AWAY_GRACE_PERIOD = 300

DARK_CHECK_INTERVAL = 3600

DARK_THRESHOLD = 20  # in lux; 60w lightbulb =~ 100

_seen_on = {}

LOGDIR = '/tmp/kh'  # ramdisk on cer, ssd on pro


def _last_changed(e):
    o = db.get_by_oid(e)
    if not o:
        _debug('no %s', e)
        return
    st = o.get('on', None)
    delay = SENSOR_BUILT_IN_DELAY.get(e, 0)
    if st:
        _seen_on[e] = True
        if not delay:
            return True
    if not e in _seen_on:
        return
    return o.get_changed('on') - delay


def _changed_within(e, x):
    c = _last_changed(e)
    if c is None or c is True:
        return c
    return time.time() - x < c

_dark_time = 0


def is_daylight():
    global _dark_time
    daylight = suncalc.within_zenith()
    o = db.get_by_oid(LS)
    if o and o.get('value', 100) <= DARK_THRESHOLD:
        _dark_time = time.time()
    if daylight and (time.time() - _dark_time) < DARK_CHECK_INTERVAL:
        daylight = False
    return daylight


class HomeState:
    lights = [LC, LK, LR, LB, LT]  # the lights we control
    lights_on = None  # lights that are always on
    sensor = None  # sensor to monitor (see within next)
    within = None  # how recently it must have been active to apply
    lights_conditional = {}  # light => (sensor, timeout) mapping

    def next_update_in_seconds(self):
        nt = None
        t = time.time()
        if self.sensor and self.within:
            c = _last_changed(self.sensor)
            if c:
                #_debug('got sensor+within: %s, %s', c, self.within)
                if c is not True:
                    nt = c + self.within + 1
                else:
                    nt = t + self.within + 1
        for sensor, (light, timeout) in self.lights_conditional.items():
            c = _last_changed(sensor)
            if c:
                if c is True:
                    nt2 = t + timeout + 1
                else:
                    nt2 = c + timeout + 1
                if nt2 < t:
                    continue
                if nt and nt2 > nt:
                    continue
                # t <= nt2 [< nt if set]
                # => take nt as the time to play
                nt = nt2
        if nt:
            d = nt - t
            if d <= 300:
                return nt - t
        return 60

    @classmethod
    def valid(cls):
        if cls.sensor and not _changed_within(cls.sensor, cls.within):
            return False
        return True
    # What to do when entering this state

    def enter(self):
        pass
    # What to do when leaving this state

    def leave(self):
        pass

    def update_lights(self):
        # We're valid in general
        daylight = is_daylight()
        h = {}
        for light in self.lights:
            state = self.get_light_state(daylight, light)
            h[light] = state
        return h

    def get_light_state(self, daylight, light):
        # XXX - some override method at some point
        if daylight and light not in DAYLIGHT_LIGHTS:
            return False
        # Unconditionally on while in this state
        if self.lights_on and light in self.lights_on:
            return True
        # Conditionally on while in this state
        override = self.lights_conditional.get(light, None)
        return override and _changed_within(*override) or False


class ProjectorState(HomeState):
    " The projector is up -> mostly dark, +- motion triggered corridor + toilet lights. "
    lights_conditional = {LC: (MSH, 30), LT: (MST, 900)}


class MobileState(HomeState):
    " Most recently seen in corridor - could be even outside. "
    within = 3600 * 3  # within 3 hours
    lights_on = [LR, LK]
    sensor = MSH
    lights_conditional = {LC: (MSH, 300), LT: (MST, 900)}


class KitchenState(HomeState):
    " Most recently seen in corridor - could be even outside. "
    within = 3600 * 3  # within 3 hours
    lights_on = [LR, LK]
    sensor = MSK


class ToiletState(HomeState):
    " Most recently activity in toilet, probably not outside. "
    within = 3600 * 2  # within 2 hours
    lights_on = [LT]
    sensor = MST
    lights_conditional = {LC: (MSH, 300)}


class AwayState(HomeState):
    # Just operate the motion sensor triggered ones, if there is motion
    # (if it gets triggered, our state should change soon-ish anyway)
    lights_conditional = {LC: (MSH, 300), LT: (MST, 3600)}


class ComputerState(HomeState):
    " Unidle at one of the computers. "
    within = 3600 * 3  # within 3 hours
    sensor = IP
    lights_on = [LR, LK]


class TimeoutState(HomeState):
    " This state we enter if one of the others actually times out (Mobile/Computer-). In that case, all we do is just pause itunes if it's running, monitor has timed out long time ago most likely. "

    def enter(self):
        #_itunes_pause()
        # n/a here, as this may run on cer
        pass


class NightState(ProjectorState):
    within = 3600 * 8
    sensor = LB
    # _only_ control toilet lightning, based on motion rules
    lights = [LT]


def _most_recent(e, *el):
    c = _last_changed(e)
    #_debug('_most_recent for %s: %s', e, c)
    if c is None:
        return False
    if c is True:
        return True
    for e2 in el:
        if e2 == e:
            continue
        c2 = _last_changed(e2)
        if c2 and (c2 is True or c2 > c):
            return False
    return True


class Home(prdb.Owner, _prdb_kh.LockedUpdated):
    state = HomeState()

    def determine_state_class(self):
        """ This is the main place where we determine the overall
        'home state'. Later on, if the chosen state is not valid
        (mostly due to timeout), we will default to HomeState which
        means all off in any case."""
        xbmc = _prdb_kh.Process.get_named('kodi')
        st = xbmc and xbmc.get('on', None)
        if st:
            return ProjectorState

        maybe_away = False
        lc_phones = [_last_changed(x) for x in PHONES]
        present_phones = [x for x in lc_phones if x is True]
        known_phones = [x for x in lc_phones if x is not None]
        if known_phones and not present_phones:
            maybe_away = True
        # XXX - this is temporary check because it seems that
        # user_active _and_ wemo events are sporadically wrong, and I
        # do not want light show at night :-p Rather leave control
        # manual, at nighttime, for now.
        if _changed_within(NightState.sensor, NightState.within) and datetime.datetime.now().hour < 10:
            return NightState

        states = [NightState, ComputerState,
                  MobileState, KitchenState, ToiletState]
        sensors = [state.sensor for state in states]
        for state in states:
            # We care about state-specific sensor being most recently
            # triggered one
            if not _most_recent(state.sensor, *sensors):
                continue
            c = _last_changed(state.sensor)
            if c is True:
                return state
            if not c:
                continue
            dt = time.time() - c
            if maybe_away and dt > AWAY_GRACE_PERIOD:
                return AwayState
            return state
        if maybe_away:
            return AwayState

    def locked_next_update_in_seconds(self):
        if self.pending:
            return 0.1  # pending state change -> 0.1 second delay
        return self.state.next_update_in_seconds()

    def some_object_changed(self):
        self.pending = True
        self.next_update_in_seconds_changed()

    def locked_update(self, *unused):
        self.pending = False
        cls = self.determine_state_class()
        if not cls or not cls.valid():
            cls = TimeoutState
        if self.state.__class__ != cls:
            if self.state:
                self.state.leave()
            self.state = cls()
            self.state.enter()
            self.o.state_name = cls.__name__
        desired_state = self.state.update_lights()
        if not desired_state:
            return
        changed_state = {}
        for name, state in desired_state.items():
            o = db.get_by_oid(name)
            if o:
                if o.get('on', None) is not state:
                    changed_state[o] = state
        if not changed_state:
            return
        _debug('changing state: %s', changed_state)
        # XXX - not elegant, but make sure the hue hasn't changed under us..
        # WeMo notifications should be ~real time, Hue NOT.
        hue_changed = [False]

        def _f(o, key, **kwargs):
            if key == 'on':
                hue_changed[0] = True
        db.object_changed.connect(_f)
        hue.get_updater().update()
        db.object_changed.disconnect(_f)
        if hue_changed[0]:
            return
        # Ok, Hue state matches what we thought it was -> go onward
        for o, state in changed_state.items():
            o.set('on', state)

        # Make sure this gets written to disk. As good point as any?
        # (if we actually had any changes..)
        logger.flush()


def _object_added(**kwargs):
    _debug('object_added %s', kwargs)


def _object_changed(o, key, old, new, **kwargs):
    _debug('object_change: %s/%s: %s=>%s %s', o.id, key, old, new, kwargs)
    h.some_object_changed()

if __name__ == '__main__':
    p = khserver.create_shared_argparser('start')
    args = khserver.parse_shared(p)

    _prdb_kh.Home.set_create_owner_instance_callback(Home)
    _debug('creating official database instance')
    db = kh.get_database()
    # Autorotate > megabyte sized ones
    if not os.path.exists(LOGDIR):
        os.mkdir(LOGDIR)
    logger = db.new_logger_to_directory(LOGDIR, autorotate=1000000)
    h = _prdb_kh.Home.new_named().get_owner()
    db.object_added.connect(_object_added)
    db.object_changed.connect(_object_changed)

    # Up to this point we do not have threads really running, so start
    # caring about locking only now..
    _prdb_kh.set_lock_check_enabled(True)

    with _prdb_kh.lock:
        khserver.start()
        if socket.gethostname() == 'poro.lan':
            poroserver.start()

    updater.add(h)

    # threads will implicitly do their stuff ..
