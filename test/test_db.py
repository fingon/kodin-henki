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
# Last modified: Mon Sep 22 19:04:45 2014 mstenber
# Edit time:     26 min
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
    kodinhenki.Object.added.connect(ma)
    kodinhenki.Object.removed.connect(mr)
    kodinhenki.Object.changed.connect(mc)
    d = kodinhenki.get_database()
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
    kodinhenki.Object.added.disconnect(ma)
    kodinhenki.Object.removed.disconnect(mr)
    kodinhenki.Object.changed.disconnect(mc)

def test_singleton_factory():
    db = kodinhenki.db.Database()
    f = kodinhenki.db.singleton_object_factory('x', kodinhenki.db.Object)
    o1 = f(db)
    o2 = f(db)
    assert o1 is o2

