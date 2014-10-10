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
# Last modified: Thu Oct  9 10:01:02 2014 mstenber
# Edit time:     102 min
#
"""

Device tracker.

It is responsible to keeping track of WeMo devices. It provides the
root 'WeMo' object for the kodinhenki database as well.

"""

MAIN_NAME='wemo'
BY_US='wemo'

import kodinhenki.db
import kodinhenki.updater as updater
import kodinhenki.util
import kodinhenki.wemo.discover as discover
import kodinhenki.wemo.device
import kodinhenki.wemo.event as event
import time

import kodinhenki.compat as compat
urljoin = compat.get_urllib_parse().urljoin

import logging
_logger = logging.getLogger('kh.wemo.device_tracker')
_debug = _logger.debug
_error = _logger.error

send_discover = kodinhenki.util.Signal()

class WeMo(kodinhenki.db.Object, updater.Updated):
    last_discovery = 0

    discover_every = 900
    devices_valid_for = 3600

    event_receiver = None
    discovery_thread = None

    def __init__(self, name, discovery_port=None, event_port=None, ip=None, remote_ip=None, *args, **kwargs):
        kodinhenki.db.Object.__init__(self, name, *args, **kwargs)
        self._devices = {}
        discover.device_seen.connect(self.device_seen)
        event.received.connect(self.device_state_event)
        if event_port is not None:
            self.event_receiver = event.start_ipv4_receiver(ip=ip, remote_ip=remote_ip, port=event_port)
        if discovery_port is not None:
            self.discovery_thread = discover.start(discovery_port)
            send_discover.connect(self.discovery_thread.send)
    def __del__(self):
        if self.discovery_thread:
            self.discovery_thread.stop()
    def on_add_to_db(self, db):
        db.object_changed.connect(self.db_state_changed)
    def on_remove_from_db(self, db):
        db.object_changed.disconnect(self.db_state_changed)
    def db_state_changed(self, o, key, by, at, old, new):
        if not (key == 'on' and by != BY_US and o.name.startswith(MAIN_NAME)):
            return
        if not o.set_state(new):
            # Do inverse set - back to old value.
            o.set(key, old, by=BY_US)

    def device_state_event(self, ip, state):
        for url, d in self._devices.items():
            o = d['o']
            if o.get('ip') == ip:
                o.set('on', state, by=BY_US)
                return
        _debug('unknown device - ip=%s' % ip)
    def device_seen(self, url, **kwargs):
        o = self._devices.get(url, None) or self.probe(url)
        if not o: return
        self._devices[url]['last_seen'] = time.time()
        _debug('marking seen: %s' % o)
    def probe(self, url):
        _debug('probing new url: %s' % url)
        db = self.get_database()
        o = kodinhenki.wemo.device.from_db_url(db, url)
        if not o: return
        if self.event_receiver is not None:
            full_url = urljoin(url, o.services['basicevent'].event_sub_url)
            s = event.Subscription(full_url, self.event_receiver)
            updater.add(s)
        self._devices[url] = {'o': o}
        return o

    # Updated interface
    def next_update_in_seconds(self):
        now = time.time()
        return (self.last_discovery + self.discover_every) - now
    def update(self):
        now = time.time()
        # Send new discover messages if need be
        if now - self.last_discovery > self.discover_every:
            _debug('sending discover')
            send_discover()
            self.last_discovery = now

        # Filter out devices that have not been seen in awhile
        for url, d in list(self._devices.items()):
            if d['last_seen'] < (now - self.devices_valid_for):
                _debug('getting rid of %s - too historic' % repr(d))
                del self._devices[url]

get = kodinhenki.db.singleton_object_factory(MAIN_NAME, WeMo)
