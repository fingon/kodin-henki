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
# Last modified: Fri Jan 23 12:04:08 2015 mstenber
# Edit time:     9 min
#
"""

Assorted utilities

"""

import socket
import threading
import prdb.util

import logging
_logger = logging.getLogger(__name__)
_debug = _logger.debug

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

import inspect

class LogLock(object):
    def __init__(self, cl):
        self.lock = cl()
    def _acquire(self, stack, who, *a, **kw):
        if self.lock.acquire(blocking=False, *a, **kw):
            _debug('%s %s (got)', stack, who)
            return True
        _debug('%s %s (pending)', stack, who)
        r = self.lock.acquire(*a, **kw)
        if r:
            _debug('%s %s (pending->got)', stack, who)
        return r
    def acquire(self, *a, **kw):
        return self._acquire(inspect.stack()[1], *a, **kw)
    def release(self):
        _debug('%s release', inspect.stack()[1])
        self.lock.release()
    def _is_owned(self):
        return self.lock._is_owned()
    def __enter__(self):
        return self._acquire(inspect.stack()[1], 'enter')
    def __exit__(self, *args):
        _debug('%s exit', inspect.stack()[1])
        self.lock.release()
        return False

def _create_lock(cl):
    return LogLock(cl)
    #return cl()


def create_rlock():
    return _create_lock(threading.RLock)
