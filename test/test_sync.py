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
# Last modified: Mon Oct 27 20:37:24 2014 mstenber
# Edit time:     14 min
#
"""

Test that the database synchronization works..

"""

import prdb
import kodinhenki.sync as sync

from mock import Mock
import threading

import logging

def test_sync():
    db1 = prdb.new()
    cl1 = db1.declare_app('simple', version=1).declare_class('dummy')
    db2 = prdb.new()
    cl2 = db2.declare_app('simple', version=1).declare_class('dummy')

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

    s1 = sync.start_server(db1, port=0)

    o1 = cl1.new_named('foo')
    o1.set('bar', 'baz')

    o2 = cl2.new_named('foo2')

    s2 = sync.start_client(db2, ('127.0.0.1', s1['port']))

    db1.commit()
    db2.commit()
    while not cl2.get_named('foo2'):
        assert e.wait(0.5)

    o2 = cl2.new_named('bar', dummyi=1, dummyf=3.14, dummys='foo')
    o2.set('bar', 'barf')
    db2.commit()

    while not cl1.get_named('bar'):
        assert e.wait(0.5)

    o1.bar = 'barf'
    db1.commit()
    while cl2.get_named('foo').bar == 'baz':
        assert e.wait(0.5)


    print('done')

    sync.stop_server(s1)
    sync.stop_client(s2)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_sync()
