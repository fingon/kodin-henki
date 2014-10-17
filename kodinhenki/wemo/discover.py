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
# Last modified: Fri Oct 17 18:59:07 2014 mstenber
# Edit time:     68 min
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

import kodinhenki.compat as compat
_socketserver = compat.get_socketserver()

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

def split_http_start_header_body_lines(data):
    data = data.decode('utf-8')
    lines = data.split('\r\n')
    start = None
    # There may be empty lines
    for i, line in enumerate(lines):
        if line.strip():
            start = line
            lines = lines[i+1:]
            break
    else:
        return
    for i, line in enumerate(lines):
        if not line.strip():
            header = lines[:i]
            lines = lines[i+1:]
            break
    else:
        header = lines
        lines = []
    return start, header, lines

def http_header_lines_to_dict(header):
    items = [line.split(':', 1) for line in header]
    items = [x for x in items if len(x) == 2]
    items = [(x.strip().lower(), y.strip()) for x, y in items]
    return dict(items)

def parse_http_header(data):
    (start, header, body) = split_http_start_header_body_lines(data)
    (proto, rc, verdict) = start.split(' ', 2)
    if rc != '200':
        return
    return http_header_lines_to_dict(header)

class DiscoveryHandler(_socketserver.BaseRequestHandler):
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
    def __init__(self, ip=None, remote_ip=None, port=None):
        ip = ip or (remote_ip and kodinhenki.util.get_ipv4_address()) or ''
        port = port or 54321
        self.server = _socketserver.UDPServer((ip, port), DiscoveryHandler)
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

def start(**kwargs):
    st = DiscoveryServiceThread(**kwargs)
    st.start()
    return st

