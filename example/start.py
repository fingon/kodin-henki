#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: cer-start.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Created:       .. sometime ~spring 2014 ..
# Last modified: Tue Oct  7 11:41:15 2014 mstenber
# Edit time:     201 min
#
"""

My home customizations (don't use this at your home ;->)

The idea is to run this at CER (which is always on, and has Python
available). It is the main responsible party for dealing with actual
control of e.g. WeMo and Belkin devices.

The other ones (poro-, fubuki-) run on computers to mainly provide the
idle or non-idle state and potentially also manipulate their own state (such as screen blanking etc) based on what is going on.

"""

import os
import time
import socket
import datetime

import logging
logger = logging.getLogger(__name__)
_debug = logger.debug

import khserver
import poroserver

import kodinhenki as kh
import kodinhenki.hue as hue
import kodinhenki.user_active as ua
import kodinhenki.updater as updater
import kodinhenki.suncalc as suncalc

khserver.start()
db = kh.get_database()

if socket.gethostname() == 'poro.lan':
    poroserver.start()

# activity sources
IP='user_active.poro'
WM='wemo.WeMo Motion'

# lights to be controlled
LB='hue.Bed'
LC='hue.Entry'
LK='hue.Kitchen'
LR='hue.Living'
WT='wemo.WeMo Toilet'

# All lights we control
ALL_LIGHTS=[LC, LK, LR, LB, WT]

# Which light do we care about when it's daylight?
DAYLIGHT_LIGHTS=[WT]
SENSOR_BUILT_IN_DELAY={IP: ua.user_active_period + 1}
#SENSOR_BUILT_IN_DELAY={}

_seen_on = {}

def _last_changed(e):
    if not db.exists(e):
        return
    o = db.get(e)
    st = o.get_defaulted('on')
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

class HomeState:
    lights = None # lights that are always on
    sensor = None # sensor to monitor (see within next)
    within = None # how recently it must have been active to apply
    overrides = {} # light => (sensor, timeout) mapping
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
        daylight = suncalc.within_zenith()
        h = {}
        for light in ALL_LIGHTS:
            state = self.get_light_state(daylight, light)
            h[light] = state
        return h
    def get_light_state(self, daylight, light):
        # XXX - some override method at some point
        if daylight and light not in DAYLIGHT_LIGHTS:
            return False
        # Unconditionally on while in this state
        if self.lights and light in self.lights:
            return True
        # Conditionally on while in this state
        override = self.overrides.get(light, None)
        return override and _changed_within(*override) or False

class ProjectorState(HomeState):
    " The projector is up -> mostly dark, +- motion triggered corridor + toilet lights. "
    overrides = {LC: (WM, 30), WT: (WM, 900)}

class MobileState(HomeState):
    " Most recently seen in corridor - could be even outside. "
    within = 3600 * 3 # within 3 hours
    lights = [LR, LK]
    sensor = WM
    overrides = {LC: (WM, 300), WT: (WM, 3600)}
    def enter(self):
        #_monitor_off() # significant power hog, waiting 3 hours not sensible
        # .. it's just 10 minutes. who cares. more annoying to have it resync
        # n/a also here, as this may run on cer
        pass

class ComputerState(HomeState):
    " Unidle at one of the computers. "
    within = 3600 * 3 # within 3 hours
    sensor = IP
    lights = [LR, LK]

class TimeoutState(HomeState):
    " This state we enter if one of the others actually times out (Mobile/Computer-). In that case, all we do is just pause itunes if it's running, monitor has timed out long time ago most likely. "
    def enter(self):
        #_itunes_pause()
        # n/a here, as this may run on cer
        pass

class NightState(HomeState):
    within = 3600 * 8
    sensor = LB
    def update_lights(self):
        # We _don't_ want to change light state when the lights have
        # been most recently manipulated via Hue Tap!
        pass

def _most_recent(e, *el):
    c = _last_changed(e)
    #_debug('_most_recent for %s: %s' % (e, c))
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

class Home(kh.Object, updater.Updated):
    state = HomeState()
    def determine_state_class(self):
        """ This is the main place where we determine the overall
        'home state'. Later on, if the chosen state is not valid
        (mostly due to timeout), we will default to HomeState which
        means all off in any case."""
        xbmc = db.get_if_exists('process.xbmc')
        st = xbmc and xbmc.get_defaulted('on')
        if st: return ProjectorState

        # XXX - this is temporary check because it seems that
        # user_active _and_ wemo events are sporadically wrong, and I
        # do not want light show at night :-p Rather leave control
        # manual, at nighttime, for now.
        if _changed_within(NightState.sensor, NightState.within) and datetime.datetime.now().hour < 10:
            return NightState

        states = [NightState, ComputerState, MobileState]
        sensors = [state.sensor for state in states]
        for state in states:
            if _most_recent(state.sensor, *sensors):
                return state
    def next_update_in_seconds(self):
        return 1 # update once a second
    def update(self, *unused):
        cls = self.determine_state_class()
        if not cls or not cls.valid():
            cls = TimeoutState
        if self.state.__class__ != cls:
            if self.state:
                self.state.leave()
            self.state = cls()
            self.state.enter()
            self.set('state_name', cls.__name__)
        desired_state = self.state.update_lights()
        if not desired_state:
            return
        changed_state = {}
        for name, state in desired_state.items():
            o = db.get_if_exists(name)
            if o:
                if o.get('on') is not state:
                    changed_state[o] = state
        if not changed_state:
            return
        _debug('changing state: %s' % repr(changed_state))
        # XXX - not elegant, but make sure the hue hasn't changed under us..
        # WeMo notifications should be ~real time, Hue NOT.
        hue_changed = [False]
        def _f(name, key, **kwargs):
            if key == 'on':
                hue_changed[0] = True
        db.object_changed.connect(_f)
        hue.get().update()
        db.object_changed.disconnect(_f)
        if hue_changed[0]:
            return
        # Ok, Hue state matches what we thought it was -> go onward
        for o, state in changed_state.items():
            o.set('on', state)

h = Home('home')
db.add_object(h)
updater.add(h)

# threads will implicitly do their stuff ..
