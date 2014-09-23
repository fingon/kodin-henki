#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: device_tracker.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Tue Sep 23 13:35:41 2014 mstenber
# Last modified: Tue Sep 23 14:42:17 2014 mstenber
# Edit time:     36 min
#
"""

Device tracker.

It is responsible to keeping track of WeMo devices. It provides the
root 'WeMo' object for the kodinhenki database as well.

"""

MAIN_NAME='wemo'
DEVICE_NAME='%s.%s'

import kodinhenki.db
import kodinhenki.util
import kodinhenki.wemo.discover
import time
from kodinhenki.compat import urlopen
from .xsd import device

namespaces = {'bd': 'urn:Belkin:device-1-0'}
#etree.register_namespace()

import logging
_debug = logging.debug
_error = logging.error

class WemoSwitch(kodinhenki.db.Object):
    def set_state(self, v):
        raise NotImplementedError

class WemoMotion(kodinhenki.db.Object):
    def set_state(self, v):
        pass

send_discover = kodinhenki.util.Signal()

class WeMo(kodinhenki.db.Object):
    last_discovery = 0

    discover_every = 900
    devices_valid_for = 3600

    def __init__(self, *args, **kwargs):
        kodinhenki.db.Object.__init__(self, *args, **kwargs)
        self._devices = {}
        kodinhenki.wemo.discover.device_seen.connect(self.device_seen)

    def device_seen(self, url, **kwargs):
        if not url in self._devices:
            o = self.probe(url)
            if o:
                self._devices[url] = {'last_seen': 0, 'o': o}
        else:
            self._devices[url]['last_seen'] = time.time()

    def update(self):
        now = time.time()
        # Send new discover messages if need be
        if now - self.last_discovery > self.discover_every:
            send_discover()
            self.last_discovery = now

        # Filter out devices that have not been seen in awhile
        for url, d in list(self._devices.items()):
            if d['last_seen'] < now - self.devices_valid_for:
                 del self._devices[url]

    def probe(self, url):
        data = urlopen(url).read()
        _debug('got data: %s' % repr(data))
        o = device.parseString(data)
        _debug('got device: %s' % repr(o))
        #raise

def _db_state_changed(o, key, by, old, new):
    if not (key == 'on' and not by and o.name.startswith(MAIN_NAME)):
        return
    o.set_state(new)

get = kodinhenki.db.singleton_object_factory(MAIN_NAME, WeMo)
kodinhenki.db.Object.changed.connect(_db_state_changed)

