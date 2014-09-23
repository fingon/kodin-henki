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
# Last modified: Tue Sep 23 11:56:24 2014 mstenber
# Edit time:     3 min
#
"""

Python 2.x / 3.x compatibility module

"""

try:
    # 2.x-ism
    import Queue
except ImportError:
    import queue as Queue
import kodinhenki.util

try:
    # 2.x-ism
    import SocketServer
except ImportError:
    import socketserver as SocketServer

