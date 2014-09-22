#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_hue.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 16:19:15 2014 mstenber
# Last modified: Mon Sep 22 17:00:25 2014 mstenber
# Edit time:     17 min
#
"""

Test code for Hue module

"""


from mock import Mock
from kodinhenki.db import Database
from kodinhenki.hue import get, HueBulb
import kodinhenki.hue

def test_hue():
    b = Mock() # bridge instance

    # fake phue
    tphue = Mock()
    kodinhenki.hue.phue = tphue

    # fake constructor for Bridge
    tphue.Bridge = Mock(return_value=b)

    l1 = Mock()
    l1.name = 'lt1'
    l2 = Mock()
    l2.name = 'lt2'
    l3 = Mock()
    l3.name = 'lt3'
    b.get_light_objects = Mock(return_value=[l1, l2, l3])
    assert len(b.get_light_objects()) == 3

    db = Database()
    h = get(db)
    assert h
    assert not h.get_lights()
    assert not h.get_light_objects()

    h.init('n/a')
    h.update()

    l = list(h.get_lights())
    assert len(l) == 3

    l = list(h.get_light_objects())
    assert len(l) >= 3

    assert isinstance(l[0], HueBulb)
    l[0].turn_on()
    assert l[0].get_light_object().on
    l[0].turn_off()
    assert not l[0].get_light_object().on

