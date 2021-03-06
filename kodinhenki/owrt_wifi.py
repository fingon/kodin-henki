#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: owrt_wifi.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Fri Oct 31 09:50:42 2014 mstenber
# Last modified: Sat May  6 12:37:39 2017 mstenber
# Edit time:     40 min
#
"""

This module keeps track of devices _when running on an OpenWrt
router_.

How does it work?

- uci export dhcp => list of known hosts (mac address + name)
(once per hour)

- ubus call hostapd.<ifname> get_clients
(once per minute or so)

"""

import json
import logging
import os
import time

import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.updater as _updater

logger = logging.getLogger(__name__)
_debug = logger.debug
_error = logger.error


DHCP_POLL_INTERVAL = 3600
WIFI_POLL_INTERVAL = 60


class OpenWrtWifiDeviceTracker(_updater.Updated):

    def __init__(self, interfaces=None):
        self._devices = {}
        self._dhcp = {}
        # Get list of interfaces
        if interfaces is None:
            prefix = 'hostapd.'
            data = list(os.popen("ubus list '%s*'" % prefix))
            interfaces = [x.replace(prefix, '').strip() for x in data]
            interfaces = [x for x in interfaces if len(x) > 0]
        self.interfaces = interfaces

    _timers = None

    @property
    def timers(self):
        if self._timers is None:
            self._timers = [_updater.Timer(DHCP_POLL_INTERVAL),
                            _updater.Timer(WIFI_POLL_INTERVAL)]
        return self._timers

    @property
    def dhcp_timer(self):
        return self.timers[0]

    @property
    def wifi_timer(self):
        return self.timers[1]

    def next_update_in_seconds(self):
        return min(self.dhcp_timer.time_left(),
                   self.wifi_timer.time_left())

    def update(self, t=None):
        if self.dhcp_timer.if_expired_reset():
            self.update_dhcp()
        if self.wifi_timer.if_expired_reset():
            t = t or time.time()
            self.update_wifi(t)
            self.update_state(t)

    def update_dhcp(self):
        df = os.popen('uci export dhcp')
        self.read_dhcp(df)

    def update_wifi(self, t):
        for interface in self.interfaces:
            wf = os.popen('ubus call hostapd.%s get_clients' % interface)
            self.read_wifi(wf, t, interface)

    def read_dhcp(self, f):
        _debug('read_dhcp')
        host = None
        self._dhcp = {}
        for line in f:
            line = line.strip()
            if line == 'config host':
                host = [None, None]
                continue
            line = line.split(' ')
            if not line:
                continue
            if line[0] != 'option':
                continue
            if len(line) != 3:
                continue
            if line[1] == 'name':
                host[0] = line[2][1:-1]
            elif line[1] == 'mac':
                host[1] = line[2][1:-1]
            else:
                continue
            if host and host[0] and host[1]:
                _debug(' added %s=%s', *tuple(host))
                self._dhcp[host[1]] = host[0]
                host = None

    def read_wifi(self, f, t, interface):
        _debug('read_wifi %s', interface)
        d = json.load(f)
        for mac in d['clients'].keys():
            n = self._dhcp.get(mac, None)
            if not n:
                _debug('  unknown mac:%s', mac)
                continue
            self._devices[n] = t

    def update_state(self, t):
        with _prdb_kh.lock:
            for n, st in self._devices.items():
                _prdb_kh.WifiDevice.new_named(n).on = (st == t)


def start(**kwargs):
    u = OpenWrtWifiDeviceTracker(**kwargs)
    _updater.add(u)
    return u
