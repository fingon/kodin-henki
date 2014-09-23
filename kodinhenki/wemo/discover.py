#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: discover.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Tue Sep 23 11:45:37 2014 mstenber
# Last modified: Tue Sep 23 13:21:23 2014 mstenber
# Edit time:     48 min
#
"""

This is (minimalist) pure Python discovery functionality.

It is implemented as a (long-lived) socket, on which new multicast
requests can be sent, and then results processed as desired. When the
listening thread is started and stopped, and how the results are
handled in threadsafe fashion are out of scope of this module.

"""

import socket
import threading

from kodinhenki.compat import *
from kodinhenki.util import Signal
import kodinhenki.util

import logging
_debug = logging.debug
_error = logging.error


SSDP_MULTICAST_IPV4_ADDRESS='239.255.255.250'
SSDP_PORT=1900

DISCOVERY_REQUEST='''M-SEARCH * HTTP/1.1
HOST:%(SSDP_MULTICAST_IPV4_ADDRESS)s:%(SSDP_PORT)d
ST:upnp:rootdevice
MX:2
MAN:"ssdp:discover"

''' % locals()
DISCOVERY_REQUEST = DISCOVERY_REQUEST.replace('\n', '\r\n')

device_seen = Signal()

def parse_http_header(data):
    data = data.decode('utf-8')
    lines = data.split('\r\n')
    lines = [line.strip() for line in lines]
    lines = list(lines)
    (proto, rc, verdict) = lines[0].split(' ')
    if rc != '200':
        return
    lines = lines[1:] # skip first entry
    items = [line.split(':', 1) for line in lines]
    items = [x for x in items if len(x) == 2]
    items = [(x.strip().lower(), y.strip()) for x, y in items]
    return dict(items)

class DiscoveryHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        _debug('DiscoveryHandler.handle')
        data = self.request[0]
        client_address = self.client_address[0]
        h = parse_http_header(data)
        if h:
            _debug('header %s' % repr(h))
            ua = h.get('x-user-agent', None)
            loc = h.get('location', None)
            if ua == 'redsonic' and loc:
                device_seen(address=client_address, url=loc, headers=h)

class DiscoveryServiceThread(threading.Thread):
    def __init__(self, port):
        ip = kodinhenki.util.get_ipv4_address()
        assert ip
        self.server = SocketServer.UDPServer((ip, port), DiscoveryHandler)
        threading.Thread.__init__(self, target=self.server.serve_forever)
        self.daemon = True
        self.send()
    def send(self):
        _debug('DiscoveryServiceThread.send')
        dest = (SSDP_MULTICAST_IPV4_ADDRESS, SSDP_PORT)
        self.server.socket.sendto(DISCOVERY_REQUEST.encode('ascii'), dest)
    def stop(self):
        self.server.shutdown()
        self.join()

def start(port=54321):
    st = DiscoveryServiceThread(port=port)
    st.start()
    return st

