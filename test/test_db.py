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
# Last modified: Wed Oct  1 13:41:33 2014 mstenber
# Edit time:     27 min
#
"""

Some tests for the db module

"""

import kodinhenki
import kodinhenki.db

from mock import Mock

import pytest

def test_base():
    db1 = kodinhenki.get_database()
    assert db1
    db2 = kodinhenki.get_database()
    assert db1 is db2

def test_o():
    ma = Mock()
    mr = Mock()
    mc = Mock()
    d = kodinhenki.get_database()
    d.object_added.connect(ma)
    d.object_removed.connect(mr)
    d.object_changed.connect(mc)
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
    assert o.get('key') == 'value'

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
    d.object_added.disconnect(ma)
    d.object_removed.disconnect(mr)
    d.object_changed.disconnect(mc)

def test_singleton_factory():
    db = kodinhenki.db.Database()
    f = kodinhenki.db.singleton_object_factory('x', kodinhenki.db.Object)
    o1 = f(db)
    o2 = f(db)
    assert o1 is o2

