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
# Last modified: Mon Oct 27 21:04:12 2014 mstenber
# Edit time:     5 min
#
"""

This is somewhat tricky to test for real..

"""

import kodinhenki
import kodinhenki.user_active as user_active

def test_user_active():
    kodinhenki.drop_database() # in case previous thing played with it
    kodinhenki.get_database() # declare schema again
    o = user_active.start('ua')
    o.o.get('on')
    o.stop()

