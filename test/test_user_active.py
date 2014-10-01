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
# Last modified: Wed Oct  1 15:38:24 2014 mstenber
# Edit time:     1 min
#
"""

This is somewhat tricky to test for real..

"""

import kodinhenki.user_active as user_active

def test_user_active():
    o = user_active.start('ua')
    o.get('on')
