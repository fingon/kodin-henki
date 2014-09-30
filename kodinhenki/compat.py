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
# Last modified: Tue Sep 30 06:44:28 2014 mstenber
# Edit time:     11 min
#
"""

Python 2.x => 3.x compatibility module

"""

import sys

def get_queue():
    try:
        import queue
    except ImportError:
        # 2.x-ism
        import Queue as queue
    return queue

def get_socketserver():
    try:
        import socketserver as _x
    except ImportError:
        # 2.x-ism
        import SocketServer as _x
    return _x


def get_urllib_request():
    try:
        import urllib.request as _x
    except ImportError:
        # 2.x-ism
        import urllib2 as _x
    return _x

def get_urllib_parse():
    try:
        import urllib.parse as _x
    except ImportError:
        # 2.x-ism
        import urlparse as _x
    return _x

def get_http_server():
    try:
        import http.server as _x
    except ImportError:
        # 2.x-ism
        import BaseHTTPServer as _x
    return _x
