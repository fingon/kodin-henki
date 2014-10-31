#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_owrt_wifi.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Fri Oct 31 09:57:40 2014 mstenber
# Last modified: Fri Oct 31 10:29:03 2014 mstenber
# Edit time:     9 min
#
"""

"""

import kodinhenki.owrt_wifi as _wifi
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki as _kh

import inspect
import os
nowfile = inspect.getfile(inspect.currentframe())
testdir = os.path.dirname(nowfile)

import os

def test_wifi():
    db = _kh.get_database()
    # Not super cool but oh well.
    def _dummy_popen(n):
        l = n.split(' ')
        if l[0] == 'uci':
            return open(os.path.join(testdir, 'uci_export.txt'))
        if l[0] == 'ubus':
            return open(os.path.join(testdir, 'hostapd_get_clients.txt'))
        raise NotImplementedError(l)
    orig_popen, os.popen = os.popen, _dummy_popen
    u = _wifi.OpenWrtWifiDeviceTracker()
    u.update()
    assert _prdb_kh.WifiDevice.get_named('iphone5').on
    assert len(u._devices) == 1
    def _dummy_popen2(n):
        l = n.split(' ')
        if l[0] == 'ubus':
            return open(os.path.join(testdir, 'hostapd_get_clients_2.txt'))
        raise NotImplementedError
    os.popen = _dummy_popen2
    u.update(t=u._last_wifi_poll + 123)
    assert not _prdb_kh.WifiDevice.get_named('iphone5').on

    os.popen = orig_popen

if __name__ == '__main__':
    test_wifi()
