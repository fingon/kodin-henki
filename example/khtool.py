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
# Last modified: Sat Oct  4 13:21:18 2014 mstenber
# Edit time:     6 min
#
"""

Minimalist tool to get, or set state of things..

"""

from __future__ import print_function
import argparse
import kodinhenki as kh
import kodinhenki.sync as sync

p = argparse.ArgumentParser(description='view/set kh state')
p.add_argument('--ip', default='127.0.0.1', type=str,
               help='address of the kh server')
p.add_argument('--port', default=31342, type=int,
               help='port of the kh server')
p.add_argument('keys', metavar='N', type=str, nargs='*',
               help='key=value, or just key to print (none = show all)')
args = p.parse_args()
db = kh.get_database()
sync.start_client(db, (args.ip, args.port))
sync.in_sync.wait()
def _dump_one(ok, kk):
    v = db.get(ok).get(kk)
    print('%s/%s=%s' % (ok, kk, v))
def _dump_object(ok):
    for kk in sorted(db.get(ok).keys()):
        _dump_one(ok, kk)
if not args.keys:
    # Show all keys!
    for k in sorted(db.keys()):
        _dump_object(k)
else:
    for key in args.keys:
        l = key.split('=', 1)
        if len(l) > 1:
            (k, v) = l
            (ok, kk) = k.split('/')
            if v == 'True':
                v = True
            elif v == 'False':
                v = False
            db.get(ok).set(kk, v)
        else:
            l = k.split('/')
            if len(l) > 1:
                _dump_one(*l)
            else:
                _dump_object(k)

