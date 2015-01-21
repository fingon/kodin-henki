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
# Last modified: Thu Jan 22 00:15:33 2015 mstenber
# Edit time:     123 min
#
"""

This is the minimalist sync module. The assumption is that we want to
make sure the prdb state is shared across multiple nodes.

To do that, we designate one node as 'master', who provides single TCP
port for connections. The TCP traffic consists of simply lines of
json, with rather simple semantics:

(cmd, args..)

where:

 cmd = log
  => args: (timestamp, oid, state-dict)

 cmd = sync_end ( start is implicit)
"""

import prdb
import kodinhenki as kh
from kodinhenki.util import Signal
import kodinhenki.prdb_kh as _prdb

import kodinhenki.compat as compat
_socketserver = compat.get_socketserver()

import threading
import socket
import json
import functools
import time

import logging
_debug = logging.debug
_error = logging.error

request_handled = Signal()
in_sync = Signal()

BY='sync'

class SyncWriter:
    stopped = False
    def __init__(self, f):
        self.f = f
        self.queue = []
        self.semaphore = threading.Semaphore()
        self.start()
    def start(self):
        self.t = threading.Thread(target=self.write_loop)
        self.t.daemon = True
        self.t.start()
    def stop(self):
        self.stopped = True
    def write(self, x):
        self.queue.append(x)
        self.semaphore.release()
    def write_loop(self):
        while not self.stopped:
            while self.queue:
                s = self.queue.pop(0)
                try:
                    self.f.write(s)
                except:
                    return
            self.semaphore.acquire()


# Note: This has to be in it's own thread or bad things happen ..
class SyncReceiver(_socketserver.StreamRequestHandler, prdb.Writer):
    def setup(self):
        _socketserver.StreamRequestHandler.setup(self)
        self.writer = SyncWriter(self.wfile)
        self.server.add_receiver(self)
        _debug('initialized %s', self)
    def handle(self):
        db = self.server.db
        while True:
            try:
                line = self.rfile.readline().decode('utf-8').strip()
            except:
                return
            if not line:
                break
            _debug('handling %s', line)
            d = json.loads(line)
            if d[0] == 'log':
                with _prdb.lock:
                    db.process_decoded_line(d[1], by=BY)
            elif d[0] == 'sync_end':
                in_sync()
            else:
                raise NotImplementedError('unknown input', d)
            request_handled()
    def handle_flushed_data(self, data):
        self.send_update_one('log', data)
    def finish(self):
        self.server.remove_receiver(self)
        _debug('finished %s', self)
    def send_update_one(self, *args):
        s = json.dumps(args)
        _debug('sending %s', s)
        b = s.encode('utf-8') + b'\n'
        self.writer.write(b)

class SyncServer(_socketserver.ThreadingMixIn, _socketserver.TCPServer):
    # .. for the socketserver superclasses ..
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, db, client, *args, **kwargs):
        self.db = db
        self._receivers = []
        self.remove_receiver = self._receivers.remove
        self.client = client
        if not client:
            _socketserver.TCPServer.__init__(self, *args, **kwargs)
        self.db.object_changed.connect(self.db_object_changed)
        #self.db.object_removed.connect(self.db_object_removed)
    def add_receiver(self, r):
        with _prdb.lock:
            self._receivers.append(r)
            self.db.dump_to_writer(r)
        r.send_update_one('sync_end')
    def db_object_changed(self, o, key, by, when, old, new):
        if self.client and by == BY: return

        # Wonder if these should be buffered.. nahh..
        for r in self._receivers:
            r.send_update_one('log', (when, o.id, {key: new}))


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

