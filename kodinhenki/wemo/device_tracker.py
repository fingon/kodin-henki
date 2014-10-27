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
# Last modified: Mon Oct 27 21:11:14 2014 mstenber
# Edit time:     122 min
#
"""

Device tracker.

It is responsible to keeping track of WeMo devices. It provides the
root 'WemoTracker' object for the kodinhenki database as well.

"""

import prdb
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.updater as updater
import kodinhenki.util
import kodinhenki.wemo.discover as discover
import kodinhenki.wemo.device
import kodinhenki.wemo as _wemo
import kodinhenki.wemo.event as event
import time

import kodinhenki.compat as compat
urljoin = compat.get_urllib_parse().urljoin

import logging
_logger = logging.getLogger('kh.wemo.device_tracker')
_debug = _logger.debug
_error = _logger.error

send_discover = kodinhenki.util.Signal()

class WemoTracker(prdb.Owner, updater.Updated):
    last_discovery = 0

    discover_every = 900
    devices_valid_for = 3600

    event_receiver = None
    discovery_thread = None

    def init(self):
        self._devices = {}
        discover.device_seen.connect(self.device_seen)
        event.received.connect(self.device_state_event)
    def set_event_port(self, event_port, **kwargs):
        self.event_receiver = event.start_ipv4_receiver(port=event_port, **kwargs)
    def set_discovery_port(self, discovery_port, **kwargs):
        self.discovery_thread = discover.start(port=discovery_port, **kwargs)
        send_discover.connect(self.discovery_thread.send)
    def __del__(self):
        if self.discovery_thread:
            self.discovery_thread.stop()
    def device_state_event(self, ip, state):
        for url, d in self._devices.items():
            o = d['o']
            if o.ip == ip:
                o.o.set('on', state, by=_wemo.BY)
                return
        _debug('unknown device - ip=%s' % ip)
    def device_seen(self, url, **kwargs):
        o = self._devices.get(url, None) or self.probe(url)
        if not o: return
        self._devices[url]['last_seen'] = time.time()
        _debug('marking seen: %s' % o)
    def probe(self, url):
        _debug('probing new url: %s' % url)
        o = kodinhenki.wemo.device.from_url(url)
        if not o: return
        if self.event_receiver is not None:
            full_url = urljoin(url, o.services['basicevent'].event_sub_url)
            s = event.Subscription(full_url, self.event_receiver)
            updater.add(s)
            # Even if we reuse the object (and we should
            # have only one device per physical object), re-probing
            # should not duplicate subscriptions. So kill the subscription.
            if o._subscription:
                updater.remove(o._subscription)
            o._subscription = s
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

_prdb_kh.WemoTracker.set_create_owner_instance_callback(WemoTracker)


def get(event_port=None, discovery_port=None, **ipargs):
    o = _prdb_kh.WemoTracker.new_named().get_owner()
    assert o
    if event_port:
        o.set_event_port(event_port, **ipargs)
    if discovery_port:
        o.set_discovery_port(discovery_port, **ipargs)
    return o
