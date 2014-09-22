#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: cer-start.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Created:       .. sometime ~spring 2014 ..
# Last modified: Mon Sep 22 18:04:20 2014 mstenber
# Edit time:     122 min
#
"""

My home customizations (don't use this at your home ;->)

The idea is to run this at CER (which is always on, and has Python
available). It is the main responsible party for dealing with actual
control of e.g. WeMo and Belkin devices.

The other ones (poro-, fubuki-) run on computers to mainly provide the
idle or non-idle state and potentially also manipulate their own state (such as screen blanking etc) based on what is going on.

"""

import homeassistant as ha
import homeassistant.bootstrap
import homeassistant.components.wo as wo
import homeassistant.components.user_active as ua
import homeassistant.components
import datetime
from homeassistant.components import STATE_ON
import os

hass = homeassistant.bootstrap.from_config_file("pi.conf")

# have to handle via remote at some point
#ua.setup(hass, 'mini') # hostname

wo.setup(hass)

import logging

logger = logging.getLogger(__name__)

import suncalc # Yet another external dependency, smirk
LB='light.Bed'
LC='light.Entry'
LK='light.Kitchen'
LR='light.Living'
I='user_active.poro'
WM='wo.WeMo_Motion'
WT='wo.WeMo_Toilet'
# All lights we control
ALL_LIGHTS=[LC, LK, LR, WT]
# Which light do we care about when it's daylight?
DAYLIGHT_LIGHTS=[WT]
SENSOR_BUILT_IN_DELAY={I: ua.user_active_period + 1}
#SENSOR_BUILT_IN_DELAY={}

_seen_on = {}

def _last_changed(e):
    st = hass.states.get(e)
    delay = SENSOR_BUILT_IN_DELAY.get(e, 0)
    if st and st.state in [STATE_ON]:
        _seen_on[e] = True
        if not delay:
            return True
    if not e in _seen_on:
        return
    if st:
        return st.last_changed - datetime.timedelta(seconds=delay)

def _changed_within(e, x):
    c = _last_changed(e)
    if c is None or c is True:
        return c
    return (datetime.datetime.now() - datetime.timedelta(seconds=x)) < c

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
        for light in ALL_LIGHTS:
            state = self.get_light_state(daylight, light)
            data = {homeassistant.components.ATTR_ENTITY_ID: e}
            if state:
                homeassistant.components.turn_on(hass, **data)
            else:
                homeassistant.components.turn_off(hass, **data)
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
        pass

class ComputerState(HomeState):
    " Unidle at one of the computers. "
    within = 3600 * 3 # within 3 hours
    sensor = I
    lights = [LR, LK]

class TimeoutState(HomeState):
    " This state we enter if one of the others actually times out (Mobile/Computer-). In that case, all we do is just pause itunes if it's running, monitor has timed out long time ago most likely. "
    def enter(self):
        _itunes_pause()

def _most_recent(e, *el):
    c = _last_changed(e)
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

class Home:
    state = HomeState()
    def determine_state_class(self):
        """ This is the main place where we determine the overall
        'home state'. Later on, if the chosen state is not valid
        (mostly due to timeout), we will default to HomeState which
        means all off in any case."""
        st = hass.states.get('process.xbmc')
        if st and st.state == STATE_ON: return ProjectorState
        _sources = (WM, I)
        if _most_recent(I, *_sources): return ComputerState
        if _most_recent(WM, *_sources): return MobileState
    def update(self, *unused):
        cls = self.determine_state_class()
        if not cls or not cls.valid():
            cls = TimeoutState
        if self.state.__class__ != cls:
            if self.state:
                self.state.leave()
            self.state = cls()
            self.state.enter()
            hass.states.set('home', cls.__name__)
        self.state.update_lights()

h = Home()
hass.track_time_change(h.update)
hass.bus.listen(ha.EVENT_STATE_CHANGED, h.update)

logger.info('ha.start_home_assistant')
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)
hass.start()
hass.block_till_stopped()
