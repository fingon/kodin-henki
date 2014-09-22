#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_db.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 14:53:31 2014 mstenber
# Last modified: Mon Sep 22 15:51:08 2014 mstenber
# Edit time:     20 min
#
"""

Some tests for the db module

"""

import kodinhenki
import kodinhenki.db

from mock import Mock

def test_base():
    db1 = kodinhenki.getDatabase()
    assert db1
    db2 = kodinhenki.getDatabase()
    assert db1 is db2

def test_o():
    ma = Mock()
    mr = Mock()
    mc = Mock()
    kodinhenki.Object.added.connect(ma)
    kodinhenki.Object.removed.connect(mr)
    kodinhenki.Object.changed.connect(mc)
    d = kodinhenki.getDatabase()
    # Should raise exception if no such object found
    try:
        d.get(name='foo')
        raise
    except KeyError:
        pass
    assert not ma.called
    d.add(name='foo', key='value')
    assert ma.called
    assert not mr.called
    assert not mc.called


    # Make sure change notifications also work
    o = d.get(name='foo')
    assert o
    v = 'v'
    o.set('k', v)
    assert mc.called
    mc.reset_mock()
    assert not mc.called
    o.set('k', v)
    assert not mc.called
    v = 'v2'
    o.set('k', v)
    assert mc.called

    try:
        o.get_changed('k2')
        raise
    except KeyError:
        pass
    dt = o.get_changed('k')
    assert dt
    assert o.get('k') == v

    # Make sure removal notification works
    d.remove(name='foo')
    assert mr.called

    # Remove listeners
    kodinhenki.Object.added.disconnect(ma)
    kodinhenki.Object.removed.disconnect(mr)
    kodinhenki.Object.changed.disconnect(mc)

def test_signal():
    s = kodinhenki.db.Signal()
    m1 = Mock()
    m2 = Mock()
    s.connect(m1)
    s.connect(m2)
    s()
    assert m1.called and m2.called
    m1.reset_mock()
    m2.reset_mock()
    s.disconnect(m2)
    s()
    assert m1.called and not m2.called

