#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_user_active.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Wed Oct  1 15:36:37 2014 mstenber
# Last modified: Wed Jan  7 15:04:34 2015 mstenber
# Edit time:     6 min
#
"""

This is somewhat tricky to test for real..

"""

import kodinhenki
import kodinhenki.user_active as user_active
import kodinhenki.prdb_kh as _prdb

def test_user_active():
    _old = _prdb.set_lock_check_enabled(True)
    with _prdb.lock:
        kodinhenki.drop_database() # in case previous thing played with it
        kodinhenki.get_database() # declare schema again
    o = user_active.start('ua')
    with _prdb.lock:
        o.o.get('on')
    o.stop()
    _prdb.set_lock_check_enabled(_old)

