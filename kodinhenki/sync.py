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
# Last modified: Sat Sep  5 21:26:19 2015 mstenber
# Edit time:     220 min
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
import pysyma.shsp
import pysyma.si

import threading
import socket
import json
import functools
import time
from collections import defaultdict

import logging
_debug = logging.debug
_error = logging.error

request_handled = Signal()
in_sync = Signal()

BY='sync'


class Syncer(pysyma.shsp.SHSPSubscriber):
    def __init__(self, db, p):
        self.db = db
        self.p = p
        # local -> remote
        db.object_changed.connect(self.db_object_changed)
        p.add_subscriber(self)
        self.updates = []
        self.oidk2ts = {}
        self.hostname = '%s/%d' % (socket.gethostname(), p.sys.get_port())
        if not self.p.read_only:
            self.p.update_dict(dict(hostname=self.hostname))
        with _prdb.lock:
            self.db.commit()
            self.db.dump_to_writer(self)
    # Writer interface of prdb.Writer
    def flush_one(self):
        pass
    def write(self, oid, key, new, when):
        if oid[0] == '_': return
        skey = '%s/%s' % (oid, key)
        self.updates.append((({skey : new},), {'ts': when}))
        if len(self.updates) == 1:
            self.p.sys.schedule(0, self.push_updates)
    def network_consistent_event(self, c):
        if c:
            in_sync()
    def db_object_changed(self, o, key, by, when, old, new):
        if by == BY: return
        self.write(o.id, key, new, when)
    def push_updates(self):
        l, self.updates = self.updates, []
        for a, kwa in l:
            self.p.update_dict(*a, **kwa)
    def dict_update_event(self, n, od, nd):
        if n is self.p.own_node: return
        if nd.get('hostname', [None, ''])[1] == self.hostname: return
        ts2d = defaultdict(dict)
        for sk, (ts, v) in nd.items():
            if not sk.startswith('.'): continue
            oid, k = sk.split('/')
            ts2d[oid,ts][k] = v
            self.oidk2ts[sk] = ts
        for sk in set(od.keys()).difference(set(nd.keys())):
            if not sk.startswith('.'): continue
            ts = self.oidk2ts.pop(sk)
            oid, k = sk.split('/')
            ts2d[oid,ts][k] = None
        for (oid, ts), d in sorted(ts2d.items(), key=lambda k:k[0][1]):
            line = (ts, oid, d)
            _debug('%s dict_update_event line:%s', self, line)
            with _prdb.lock:
                self.db.process_decoded_line(line, by=BY)
                for k, v in d.items():
                    if v is None:
                        o = self.db.get_by_oid(oid)
                        v = o.get(k, None)
                        if v is not None:
                            self.write(oid, k, v, o.get_changed(k))
        request_handled()

def _shared_start(db, si, p, **kw):
    sync = Syncer(db, p)
    t = threading.Thread(target=si.loop)
    t.daemon = True
    t.start()
    return dict(si=si, p=p, t=t, sync=sync, **kw)

def start(db=None, **kw):
    db = db or kh.get_database()
    si = pysyma.si.HNCPSystemInterface()
    p = si.create_dncp(pysyma.shsp.SHSP, **kw)
    return _shared_start(db, si, p)

def stop(s):
    s['si'].stop()
    s['t'].join()

# TBD: Should these backwards compatible APIs be killed?
def start_server(db=None, ip='::1', port=kh.PORT):
    db = db or kh.get_database()
    si = pysyma.si.HNCPSystemInterface()
    # ip is ignored
    s = si.create_socket(port=port)
    p = pysyma.shsp.SHSP(sys=s)
    s.set_dncp_unicast_listen(p)
    return _shared_start(db, si, p, port=s.get_port())

def start_client(db, addr):
    if addr[0] == '127.0.0.1':
        addr = ('::1', addr[1])
    si = pysyma.si.HNCPSystemInterface()
    s = si.create_socket(port=0)
    p = pysyma.shsp.SHSP(sys=s)
    s.set_dncp_unicast_connect(p, addr)
    return _shared_start(db, si, p)

stop_client = stop
stop_server = stop
