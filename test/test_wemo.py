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
# Last modified: Tue Sep 23 12:51:08 2014 mstenber
# Edit time:     13 min
#
"""

"""

import kodinhenki.wemo.discover as discover
from mock import Mock
import threading
import time
import logging

def test_discover(caplog):
    if caplog: caplog.setLevel(logging.DEBUG)
    s = threading.Semaphore(0)
    device_seen = Mock()
    discover.device_seen.connect(device_seen)
    def _foo(**kwargs):
        s.release()
    discover.device_seen.connect(_foo)
    o = discover.start()
    for i in range(50):
        if s.acquire(blocking=False):
            break
        time.sleep(0.01)
    o.stop()
    assert device_seen.called

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_discover(None)
