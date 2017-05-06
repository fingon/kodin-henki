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
# Last modified: Sat May  6 12:39:28 2017 mstenber
# Edit time:     13 min
#
"""

"""

import os
import time

import kodinhenki as _kh
import kodinhenki.owrt_wifi as _wifi
import kodinhenki.prdb_kh as _prdb_kh

from mock import patch

testdir = os.path.dirname(__file__)


def test_wifi():
    _kh.get_database()
    # Not super cool but oh well.

    def _dummy_popen(n):
        l = n.split(' ')
        if l[0] == 'uci':
            return open(os.path.join(testdir, 'uci_export.txt'))
        if l[0] == 'ubus':
            return open(os.path.join(testdir, 'hostapd_get_clients.txt'))
        raise NotImplementedError(l)
    with patch('os.popen', new=_dummy_popen):
        u = _wifi.OpenWrtWifiDeviceTracker()
        u.update()
        assert _prdb_kh.WifiDevice.get_named('iphone5').on
        assert len(u._devices) == 1

    def _dummy_popen2(n):
        l = n.split(' ')
        if l[0] == 'ubus':
            return open(os.path.join(testdir, 'hostapd_get_clients_2.txt'))
        raise NotImplementedError
    with patch('os.popen', new=_dummy_popen2):
        u.update_wifi(t=time.time() + 123)
        u.update_state(t=time.time() + 123)
        assert not _prdb_kh.WifiDevice.get_named('iphone5').on

if __name__ == '__main__':
    test_wifi()
