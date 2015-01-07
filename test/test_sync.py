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
# Last modified: Wed Jan  7 14:38:30 2015 mstenber
# Edit time:     24 min
#
"""

Test that the database synchronization works..

"""

import prdb
import kodinhenki.sync as sync
import kodinhenki.prdb_kh as _prdb

from mock import Mock
import threading

import logging

def test_sync():
    _old = _prdb.set_lock_check_enabled(True)

    with _prdb.lock:
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

    with _prdb.lock:
        o1 = cl1.new_named('foo')
        o1.set('bar', 'baz')

        o2 = cl2.new_named('foo2')

    s2 = sync.start_client(db2, ('127.0.0.1', s1['port']))

    with _prdb.lock:
        db1.commit()
        db2.commit()

    def _locked_wait(cond):
        while True:
            with _prdb.lock:
                if cond():
                    return
            assert e.wait(0.5)

    _locked_wait(lambda :cl2.get_named('foo2'))

    with _prdb.lock:
        o2 = cl2.new_named('bar', dummyi=1, dummyf=3.14, dummys='foo')
        o2.set('bar', 'barf')
        db2.commit()

    _locked_wait(lambda :cl1.get_named('bar'))

    with _prdb.lock:
        o1.bar = 'barf'
        db1.commit()

    _locked_wait(lambda :cl2.get_named('foo').bar != 'baz')

    print('done')

    sync.stop_server(s1)
    sync.stop_client(s2)

    _prdb.set_lock_check_enabled(_old)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_sync()
