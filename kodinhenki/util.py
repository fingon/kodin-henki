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
# Last modified: Mon Oct 27 19:34:24 2014 mstenber
# Edit time:     6 min
#
"""

Assorted utilities

"""

import socket
import threading
import prdb.util

# Import Signal from elsewhere :-p
Signal = prdb.util.Signal

def _get_ip_address(af, dest):
    s = socket.socket(af, socket.SOCK_DGRAM)
    try:
        s.connect((dest, 1234))
        return s.getsockname()[0]
    except socket.error:
        pass

# Google DNS by default
def get_ipv4_address(remote_ip='8.8.8.8'):
    return _get_ip_address(socket.AF_INET, remote_ip)

def get_ipv6_address(remote_ip='2600::'):
    # Sprint somewhere, but main point is that it's GUA
    return _get_ip_address(socket.AF_INET6, remote_ip)

