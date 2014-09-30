#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: event.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Tue Sep 30 06:34:17 2014 mstenber
# Last modified: Tue Sep 30 09:08:37 2014 mstenber
# Edit time:     52 min
#
"""

Simple subscriber + event handling for a single service.

"""

import kodinhenki.updater
import kodinhenki.wemo.discover
from xml.dom.minidom import parseString

import kodinhenki.compat
_request = kodinhenki.compat.get_urllib_request()
_socketserver = kodinhenki.compat.get_socketserver()
_httpserver = kodinhenki.compat.get_http_server()
urlopen = _request.urlopen

from kodinhenki.util import Signal
subscribed = Signal()
received = Signal()

import logging
_debug = logging.debug
_error = logging.error

import threading

class CustomMethodRequest(_request.Request):
    SUBSCRIBE='SUBSCRIBE'
    UNSUBSCRIBE='UNSUBSCRIBE'
    def __init__(self, method, url, *args, **kwargs):
        self.method = method
        _request.Request.__init__(self, url, *args, **kwargs)
    def get_method(self):
        if self.method:
            return self.method
        return _request.Request.get_method(self)

class EventHandler(_httpserver.BaseHTTPRequestHandler):
    def do_NOTIFY(self):
        _debug('EventHandler.handle')
        _debug(' client_address:%s' % repr(self.client_address))
        (ip, port) = self.client_address
        _debug(' headers:%s' % repr(self.headers))
        data = self.rfile.read()
        _debug(' data:%s' % repr(data))
        doc = parseString(data)
        # XXX - if we wanted to be generic, we could do magic here.
        # However, as I cannot be bothered, I am just looking for the
        # BinaryState
        state = kodinhenki.wemo.device._wemo_string(doc, 'BinaryState', None)
        if state is not None:
            if state == '0':
                received(ip=ip, state=False)
            elif state == '1':
                received(ip=ip, state=True)
            else:
                raise AssertionError('Weird state: %s' % state)
        self.send_response(200)

def start_ipv4_receiver(ip=None, port=0, remote_ip=None, **kwargs):
    if not ip:
        assert remote_ip
        ip = kodinhenki.util.get_ipv4_address(remote_ip=remote_ip)
        assert ip
    server = _httpserver.HTTPServer((ip, port), EventHandler)
    st = threading.Thread(target=server.serve_forever)
    st.daemon = True
    st.start()
    return {'thread': st, 'server': server}

class Subscription(kodinhenki.updater.Updated):
    subscription_valid_until = 0
    default_seconds = 60
    fails = 0
    def __init__(self, url, receiver):
        self.url = url
        self.receiver = receiver
    def next_update_in_seconds(self):
        now = time.time()
        return now - self.subscription_valid_until
    def update(self):
        server_address = self.receiver['server'].server_address
        _debug('subscribing to %s (and receiving at %s)' % (self.url, server_address))
        (ip, port) = server_address
        headers = {'Timeout': 'Second-%d' % self.default_seconds,
                   'Callback': '<http://%s:%d>' % (ip, port),
                   'NT': 'upnp:event',
                   }
        req = CustomMethodRequest('SUBSCRIBE', self.url, headers=headers)
        o = urlopen(req)
        data = o.read()
        info = dict(o.info().items()) # = header as a dict
        for k, v in info.items():
            if k.lower() == 'timeout':
                SECONDS_PREFIX='second-'
                if v[:len(SECONDS_PREFIX)].lower() == SECONDS_PREFIX:
                    v = v[len(SECONDS_PREFIX):]
                    seconds = int(v)
                    break
        else:
            # retry in a while..
            self.fails = self.fails + 1
            return 5 * 2 ** self.fails
        self.fails = 0
        _debug(' %s/%s' % (info, data))
        subscribed(url=self.url, seconds=seconds)
        return seconds

def subscribe(url, receiver):
    s = Subscription(url, receiver)
    kodinhenki.updater.add(s)
    return s
