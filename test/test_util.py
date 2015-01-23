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
# Last modified: Thu Jan 22 14:38:41 2015 mstenber
# Edit time:     3 min
#
"""

Tests for util.py

"""

import kodinhenki.util

def test_get_ip_address():
    a4 = kodinhenki.util.get_ipv4_address()
    a6 = kodinhenki.util.get_ipv6_address()

