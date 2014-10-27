#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_wemo.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Tue Sep 23 11:46:46 2014 mstenber
# Last modified: Mon Oct 27 21:01:46 2014 mstenber
# Edit time:     61 min
#
"""

"""

import kodinhenki
import kodinhenki.wemo as wemo
import kodinhenki.wemo.discover as discover
import kodinhenki.wemo.device as device
import kodinhenki.wemo.event as event
import kodinhenki.wemo.device_tracker as dt

from mock import Mock
import threading
import time
import logging

import kodinhenki.compat as compat
urljoin = compat.get_urllib_parse().urljoin

def test_wemo(caplog):
    if caplog: caplog.setLevel(logging.DEBUG)
    kodinhenki.drop_database() # in case previous thing played with it
    db = kodinhenki.get_database() # not really used, but needed to populate schema
    w = dt.get()
    device_seen = Mock()
    discover.device_seen.connect(device_seen)
    r = event.start_ipv4_receiver(port=8989, remote_ip='1.2.3.4')
    switch = [None]
    def _event_received(**kwargs):
        print('event.received', kwargs)
    event.received.connect(_event_received)
    _event_subscribed = Mock()
    event.subscribed.connect(_event_subscribed)
    def _device_added(o):
        print('device.added', o)
        #o.services['basicevent'].populate()
        #o.services['basicevent'].GetSerialNo()
        print(o.services['basicevent'].GetBinaryState())
        #print(o.services['basicevent'].GetLogFileURL())
        url = urljoin(o.url, o.services['basicevent'].event_sub_url)
        s = event.Subscription(url, r)
        assert s.next_update_in_seconds() < 0
        s.update()
        assert s.next_update_in_seconds() > 0
        if isinstance(o, device.WemoSwitch):
            switch[0] = o
    device.device_added.connect(_device_added)
    def _device_seen(address, url, **kwargs):
        print('device.seen', address, url)
    discover.device_seen.connect(_device_seen)
    o = discover.start()
    assert discover.device_seen.wait(1)
    o.stop()
    assert device_seen.called
    if caplog is None:
        assert _event_subscribed.called or event.subscribed.wait(timeout=60)
        assert switch[0]
        switch = switch[0]
        print('toggling on')
        switch.turn_on()
        time.sleep(1)
        print('toggling off')
        switch.turn_off()
        time.sleep(1)
        print('done')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_wemo(None)
