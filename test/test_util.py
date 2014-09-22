#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_util.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 19:04:40 2014 mstenber
# Last modified: Mon Sep 22 19:05:28 2014 mstenber
# Edit time:     1 min
#
"""

Tests for util.py

"""

import kodinhenki.util
from mock import Mock

def test_signal():
    s = kodinhenki.util.Signal()
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

