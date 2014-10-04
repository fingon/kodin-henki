#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_updater.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Sat Oct  4 12:26:36 2014 mstenber
# Last modified: Sat Oct  4 12:29:37 2014 mstenber
# Edit time:     2 min
#
"""

Test the updater class.

"""

import kodinhenki.updater as updater
from mock import Mock
import time

DELAY=0.01
def test_updater():
    m = Mock()
    class ShortWaiter(updater.Updated):
        def next_update_in_seconds(self):
            return DELAY
        def update(self):
            m()
    sw = ShortWaiter()

    updater.add(sw)
    assert not updater.is_empty()
    assert not m.called
    time.sleep(DELAY * 2)
    assert m.called
    updater.remove(sw)
    assert updater.is_empty()

    updater.add(sw)
    updater.remove_all()
    assert updater.is_empty()
