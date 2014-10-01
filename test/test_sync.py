#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_sync.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Wed Oct  1 14:08:10 2014 mstenber
# Last modified: Wed Oct  1 14:46:07 2014 mstenber
# Edit time:     8 min
#
"""

Test that the database synchronization works..

"""

import kodinhenki.db as db
import kodinhenki.sync as sync

from mock import Mock
import threading

import logging

def test_sync():
    db1 = db.Database()
    db2 = db.Database()

    ma = Mock()
    mr = Mock()
    mc = Mock()
    db2.object_added.connect(ma)
    db2.object_removed.connect(mr)
    db2.object_changed.connect(mc)

    e = threading.Event()

    def _f():
        e.set()

    sync.request_handled.connect(_f)

    s1 = sync.start_server(db1)

    o1 = db1.add('foo')
    o1.set('bar', 'baz')

    o2 = db1.add('foo2')

    s2 = sync.start_client(db2, ('127.0.0.1', s1['port']))

    while not db2.exists('foo2'):
        assert e.wait(0.5)

    o2 = db2.add('bar', dummyi=1, dummyf=3.14, dummys='foo')
    o2.set('bar', 'barf')
    while not db1.exists('bar'):
        assert e.wait(0.5)

    # zap in origin
    print('waiting remove 1')
    db1.remove('foo')
    while db2.exists('foo'):
        assert e.wait(0.5)

    # zap in origin
    print('waiting remove 2')
    db2.remove('bar')
    while db1.exists('foo'):
        assert e.wait(0.5)

    # zap in non-origin
    print('waiting remove 3')
    db2.remove('foo2')
    while db1.exists('foo2'):
        assert e.wait(0.5)
    print('done')

    sync.stop_server(s1)
    sync.stop_client(s2)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_sync()
