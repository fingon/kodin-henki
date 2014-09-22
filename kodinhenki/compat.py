#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: compat.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 19:06:38 2014 mstenber
# Last modified: Mon Sep 22 19:06:51 2014 mstenber
# Edit time:     1 min
#
"""

Python 2.x / 3.x compatibility module

"""

try:
    import Queue
except ImportError:
    import queue as Queue
import kodinhenki.util

