#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: sync.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Wed Oct  1 13:15:48 2014 mstenber
# Last modified: Sat Oct  4 12:19:15 2014 mstenber
# Edit time:     68 min
#
"""

This is the minimalist sync module. The assumption is that we want to
make sure the kodinhenki.db state is shared across multiple nodes.

To do that, we designate one node as 'master', who provides single TCP
port for connections. The TCP traffic consists of simply lines of
json, with rather simple semantics:

(cmd, args..)

where:

 cmd = add
  => args: name

 cmd = remove
  => args: name

 cmd = set
  => args: name, k, v, when [by is lost]

 cmd = sync_end ( start is implicit)
"""

import kodinhenki as kh
import kodinhenki.db as db
from kodinhenki.util import Signal

import kodinhenki.compat as compat
_socketserver = compat.get_socketserver()

import threading
import socket
import json
import functools

import logging
_debug = logging.debug
_error = logging.error

request_handled = Signal()
in_sync = Signal()

BY='sync'

# Note: This has to be in it's own thread or bad things happen ..
class SyncReceiver(_socketserver.StreamRequestHandler):
    def setup(self):
        _socketserver.StreamRequestHandler.setup(self)
        self.server.add_receiver(self)
        _debug('initialized %s' % self)
    def handle(self):
        while True:
            line = self.rfile.readline().decode('utf-8').strip()
            if not line:
                break
            _debug('handling %s' % line)
            d = json.loads(line)
            if d[0] == 'add':
                if not self.server.db.exists(d[1]):
                    self.server.db.add(d[1], by=BY)
            elif d[0] == 'remove':
                self.server.db.remove(d[1], by=BY)
            elif d[0] == 'set':
                (n, k, v, when) = d[1:]
                self.server.db.get(n).set(k, v, by=BY, now=when)
            elif d[0] == 'sync_end':
                in_sync()
            else:
                raise NotImplementedError('unknown input', d)
            request_handled()
    def finish(self):
        self.server.remove_receiver(self)
        _debug('finished %s' % self)

class SyncServer(_socketserver.ThreadingMixIn, _socketserver.TCPServer):
    daemon_threads = True
    update_on_connect = True
    def __init__(self, db, client, *args, **kwargs):
        self.db = db
        self._receivers = []
        self.remove_receiver = self._receivers.remove
        if not client:
            _socketserver.TCPServer.__init__(self, *args, **kwargs)
        else:
            self.update_on_connect = False
        self.db.object_added.connect(self.db_object_added)
        self.db.object_changed.connect(self.db_object_changed)
        self.db.object_removed.connect(self.db_object_removed)
    def add_receiver(self, r):
        self._receivers.append(r)
        if not self.update_on_connect:
            return
        # Replay current database state for non-sync sourced things
        cb = functools.partial(self.send_update_one, r)
        for n, o in self.db.items():
            self.produce_updates(o, cb)
        self.send_update_one(r, 'sync_end')
    def produce_updates(self, o, cb):
        cb('add', o.name)
        for k, (v, when, by) in o.items():
            cb('set', o.name, k, v, when)
    def db_object_added(self, o, by):
        if by == BY: return # avoid recursion
        self.produce_updates(o, self.send_update)
    def db_object_changed(self, o, key, by, at, old, new):
        if by == BY: return # avoid recursion
        self.send_update('set', o.name, key, new, at)
    def db_object_removed(self, o, by):
        if by == BY: return # avoid recursion
        self.send_update('remove', o.name)
    def send_update(self, *args):
        # Inefficient, but makes life much simpler
        for r in self._receivers:
            self.send_update_one(r, *args)
    def send_update_one(self, r, *args):
        s = json.dumps(args)
        _debug('sending %s' % s)
        b = s.encode('utf-8') + b'\n'
        r.wfile.write(b)


def start_server(db=None, ip='', port=kh.PORT):
    db = db or kh.get_database()
    server = SyncServer(db, False, (ip, port), SyncReceiver)
    st = threading.Thread(target=server.serve_forever)
    st.daemon = True
    st.start()
    return {'thread': st, 'server': server, 'port': server.server_address[1]}

def start_client(db, addr):
    server = SyncServer(db, True)
    o = {'alive': True}
    def _f():
        while o['alive']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(addr)
                o['sock'] = sock
            except:
                _error("socket-connect failed, retrying in a second")
                time.sleep(1)
                continue
            SyncReceiver(sock, None, server)
            _error("client connection died(?), retrying in a second")
            time.sleep(1)
    ct = threading.Thread(target=_f)
    ct.daemon = True
    ct.start()
    o['thread'] = ct
    return o

def stop_server(s):
    s['server'].shutdown()

def stop_client(s):
    s['alive'] = False
    sock = s.get('sock', None)
    if sock:
        sock.close()
    # TBD: is there some way to force faster closure of client?

