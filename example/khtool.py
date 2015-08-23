#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: khtool.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Sat Oct  4 13:01:00 2014 mstenber
# Last modified: Sun Aug 23 12:34:21 2015 mstenber
# Edit time:     18 min
#
"""

Minimalist tool to get, or set state of things..

"""

from __future__ import print_function
import argparse
import kodinhenki as kh
import kodinhenki.sync as sync
import kodinhenki.prdb_kh as _prdb_kh
import time

p = argparse.ArgumentParser(description='view/set kh state')
p.add_argument('-d', '--debug', action='store_true',
               help='enable debugging')
p.add_argument('-v', '--verbose', action='store_true',
               help='verbose output')
p.add_argument('keys', metavar='N', type=str, nargs='*',
               help='key=value, or just key to print (none = show all)')
args = p.parse_args()
if args.debug:
    import logging
    logging.basicConfig(level=logging.DEBUG)
db = kh.get_database()
sync.start()
sync.in_sync.wait()
def _dump_one(ok, kk):
    o = db.get_by_oid(ok)
    v = o.get(kk)
    changed = ''
    if args.verbose:
        changed = o.get_changed(kk)
        if changed:
            changed = ' (-%d)' % (time.time() - changed)
    print('%s/%s=%s%s' % (ok, kk, v, changed))

def _dump_object(ok):
    for kk in sorted(db.get_by_oid(ok).keys()):
        if kk[0] == '_':
            continue
        _dump_one(ok, kk)

if not args.keys:
    # Show all keys!
    for k in sorted(_prdb_kh.KH.instances().as_oid_list()):
        _dump_object(k)
else:
    did_set = [False]
    def _f(**kwargs):
        did_set[0] = True
    db.object_changed.connect(_f)
    for key in args.keys:
        l = key.split('=', 1)
        if len(l) > 1:
            (k, v) = l
            (ok, kk) = k.split('/')
            if v == 'True':
                v = True
            elif v == 'False':
                v = False
            db.get_by_oid(ok).set(kk, v)
        else:
            l = k.split('/')
            if len(l) > 1:
                _dump_one(*l)
            else:
                _dump_object(k)
    if did_set[0]:
        # Wait for the change to propagate..
        sync.request_handled.wait()
