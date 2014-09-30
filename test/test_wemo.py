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
# Last modified: Tue Sep 30 08:42:06 2014 mstenber
# Edit time:     38 min
#
"""

"""

import kodinhenki
import kodinhenki.wemo as wemo
import kodinhenki.wemo.discover as discover
import kodinhenki.wemo.device as device
import kodinhenki.wemo.event as event
from mock import Mock
import threading
import time
import logging

import kodinhenki.compat as compat
urljoin = compat.get_urllib_parse().urljoin

def test_wemo(caplog):
    if caplog: caplog.setLevel(logging.DEBUG)
    db = kodinhenki.get_database()
    w = wemo.get(db)
    s_device_seen = threading.Semaphore(0)
    s_event = threading.Semaphore(0)
    device_seen = Mock()
    discover.device_seen.connect(device_seen)
    r = event.start_ipv4_receiver(port=8989, remote_ip='1.2.3.4')
    def _barf(**kwargs):
        print('event', kwargs)
        s_event.release()
    event.received.connect(_barf)

    def _baz(**kwargs):
        print('subscribed', kwargs)
    event.subscribed.connect(_baz)
    def _bar(o):
        #o.services['basicevent'].populate()
        #o.services['basicevent'].GetSerialNo()
        print(o.services['basicevent'].GetBinaryState())
        #print(o.services['basicevent'].GetLogFileURL())
        url = urljoin(o.url, o.services['basicevent'].event_sub_url)
        s = event.Subscription(url, r)
        s.update()
    device.device_added.connect(_bar)
    def _foo(address, url, **kwargs):
        #print(urlopen(url).read())
        s_device_seen.release()
    discover.device_seen.connect(_foo)
    o = discover.start()
    def _wait_s(s, t=1, steps=1000):
        for i in range(steps):
            if s.acquire(blocking=False):
                break
            time.sleep(1.0 * t / steps)
        else:
            raise AssertionError("wait condition not met")
    _wait_s(s_device_seen)
    o.stop()
    _wait_s(s_event, t=60)
    assert device_seen.called

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_wemo(None)
