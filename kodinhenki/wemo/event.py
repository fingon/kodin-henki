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
# Last modified: Wed Jan 28 22:05:57 2015 mstenber
# Edit time:     103 min
#
"""

Simple subscriber + event handling for a single service.

"""

import kodinhenki.updater
import kodinhenki.wemo.discover

import kodinhenki.compat
_request = kodinhenki.compat.get_urllib_request()
_socketserver = kodinhenki.compat.get_socketserver()
_httpserver = kodinhenki.compat.get_http_server()
urlopen = _request.urlopen

from kodinhenki.util import Signal
subscribed = Signal()
received = Signal()

import time
import threading
from xml.dom.minidom import parseString

import logging
_logger = logging.getLogger(__name__)
_debug = _logger.debug
_error = _logger.error


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
        _debug(' client_address:%s', self.client_address)
        (ip, port) = self.client_address
        _debug(' headers:%s', self.headers)
        lines = []
        for line in self.rfile:
            if not line.strip():
                break
            lines.append(line)
        data = b''.join(lines)
        _debug(' data:%s', data)
        doc = parseString(data)
        # XXX - if we wanted to be generic, we could do magic here.
        # However, as I cannot be bothered, I am just looking for the
        # BinaryState
        state = kodinhenki.wemo.device._wemo_string(doc, 'BinaryState', None)
        if state is not None:
            if state == '0':
                state=False
            elif state == '1':
                state=True
            else:
                raise AssertionError('Weird state: %s' % state)
        self.send_response(200, 'OK')
        data = b'<html><body>...</body></html>'
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', len(data))
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(data)
        if state is not None:
            received(ip=ip, state=state)
        _debug(' done')

class EventServer(_httpserver.HTTPServer):
    def address_string(self):
        return self.client_address[0]

def start_ipv4_receiver(ip=None, port=0, remote_ip=None, **kwargs):
    if not ip:
        assert remote_ip
        ip = kodinhenki.util.get_ipv4_address(remote_ip=remote_ip)
        assert ip
    server = EventServer((ip, port), EventHandler)
    st = threading.Thread(target=server.serve_forever)
    st.daemon = True
    st.start()
    return {'thread': st, 'server': server}

class Subscription(kodinhenki.updater.Updated):
    subscription_valid_until = 0
    default_seconds = 600
    fails = 0
    sid = None
    def __init__(self, url, receiver):
        self.url = url
        self.receiver = receiver
    def next_update_in_seconds(self):
        now = time.time()
        return self.subscription_valid_until - now
    def _subscribe(self):
        server_address = self.receiver['server'].server_address
        _debug('subscribing to %s (and receiving at %s) - sid:%s',
               self.url, server_address, self.sid)
        (ip, port) = server_address
        headers = {'Timeout': 'Second-%d' % self.default_seconds,
                   'Callback': '<http://%s:%d>' % (ip, port),
                   'NT': 'upnp:event',
                   }
        if self.sid:
            headers['SID'] = self.sid
        req = CustomMethodRequest('SUBSCRIBE', self.url, headers=headers)
        try:
            o = urlopen(req, None, 5)
            data = o.read()
            info = dict(o.info().items()) # = header as a dict
        except:
            data = b''
            info = {}
        result = {}
        _debug(' %s/%s', info, data)
        for k, v in info.items():
            kl = k.lower()
            if kl == 'timeout':
                SECONDS_PREFIX='second-'
                if v[:len(SECONDS_PREFIX)].lower() == SECONDS_PREFIX:
                    v = v[len(SECONDS_PREFIX):]
                    result['seconds'] = int(v)
                    break
            elif kl == 'sid':
                result['sid'] = v
        return result
    def update(self):
        r = self._subscribe()
        if 'seconds' not in r and self.sid:
            self.sid = None
            r = self._subscribe()
        if 'seconds' not in r:
            # retry in a while..
            self.fails = self.fails + 1
            self.subscription_valid_until = time.time() + 5 * 2 ** self.fails
            return
        seconds = r['seconds']
        sid = r.get('sid')
        self.sid = sid
        self.fails = 0
        subscribed(url=self.url, seconds=seconds, sid=sid)
        self.subscription_valid_until = time.time() + seconds - 5

def subscribe(url, receiver):
    s = Subscription(url, receiver)
    kodinhenki.updater.add(s)
    return s
