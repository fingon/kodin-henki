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
# Last modified: Sat Aug 22 11:41:55 2015 mstenber
# Edit time:     158 min
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
    def network_consistent_event(self, c):
        if c:
            in_sync()
    def db_object_changed(self, o, key, by, when, old, new):
        if by == BY: return
        skey = '%s/%s' % (o, key)
        self.p.update_dict({skey : new and new or None}, ts=when)
    def dict_update_event(self, n, od, nd):
        if n is self.p.own_node: return
        for sk, (ts, v) in nd.items():
            if not k.startswith('.kh.'): continue
            oid, k = sk.split('/')
            line = (ts, oid, {k: v})
            db.process_decoded_line(line, by=BY)
        for sk in od.keys().difference(nd.keys()):
            if not k.startswith('.kh.'): continue
            oid, k = sk.split('/')
            line = (ts, oid, {k: None})
            db.process_decoded_line(line, by=BY)
        request_handled()

def _shared_start(db, si, p, **kw):
    sync = Syncer(db, p)
    t = threading.Thread(target=si.loop)
    t.daemon = True
    t.start()
    return dict(si=si, p=p, t=t, sync=sync, **kw)

def start(db):
    si = pysyma.si.HNCPSystemInterface()
    p = si.create_dncp(pysyma.shsp.SHSP)
    return _shared_start(db, si, p)

def stop(s):
    s['si'].stop()
    # TBD: Should we close sockets too?

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
