#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: util.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 19:03:29 2014 mstenber
# Last modified: Tue Sep 23 11:53:42 2014 mstenber
# Edit time:     2 min
#
"""

Assorted utilities

"""

import socket

# Decoupled listener implementation with optional filtering
# (e.g. 'pysignal' is something like this, but Django semantics make
# it look much harder)

class Signal:
    def __init__(self):
        self._listeners = []
    def connect(self, callback, filter=None):
        self._listeners.append((callback, filter))
    def __call__(self, **kwargs):
        for fun, filter in self._listeners:
            if not filter or filter(kwargs):
                fun(**kwargs)
    def disconnect(self, callback, filter=None):
        self._listeners.remove((callback, filter))


def _get_ip_address(af, dest):
    s = socket.socket(af, socket.SOCK_DGRAM)
    try:
        s.connect((dest, 1234))
        return s.getsockname()[0]
    except socket.error:
        pass

def get_ipv4_address():
    # Google DNS
    return _get_ip_address(socket.AF_INET, '8.8.8.8')

def get_ipv6_address():
    # Sprint somewhere, but main point is that it's GUA
    return _get_ip_address(socket.AF_INET6, '2600::')

