#!/usr/bin/env python3.4
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
# Last modified: Sat Oct  4 14:13:29 2014 mstenber
# Edit time:     30 min
#
"""

Test code for Hue module

"""


from mock import Mock, patch
import kodinhenki.db
import kodinhenki.hue as hue
import time

@patch('kodinhenki.hue.phue')
def test_hue(*args):
    b = Mock() # bridge instance

    # fake phue
    tphue = hue.phue

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

    db = kodinhenki.db.Database()
    assert db
    h = hue.get(db, ip='1.2.3.4')
    assert h

    # Run update by hand
    assert h.next_update_in_seconds() < 0
    h.update()
    assert h.next_update_in_seconds() > 0

    l = list(h.get_lights())
    assert len(l) == 3

    l = list(h.get_light_objects())
    assert len(l) >= 3

    assert isinstance(l[0], hue.HueBulb)
    l[0].turn_on()
    assert l[0].get_light_object().on
    l[0].turn_off()
    assert not l[0].get_light_object().on

    assert db.get('hue.lt1')

def test_real_hue(caplog):
    # Don't run test in real unit tests, as it adds delay and annoying RL
    # state change
    if caplog is not None: return
    db = kodinhenki.db.Database()
    h = hue.get(db, ip='192.168.44.10')
    h.update()
    bed = db.get('hue.Bed')
    bed.set('on', True)
    time.sleep(1)
    bed.set('on', False)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    test_hue()
    test_real_hue(None)
