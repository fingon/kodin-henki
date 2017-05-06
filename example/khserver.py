#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: khserver.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Sat Oct  4 12:00:08 2014 mstenber
# Last modified: Sat May  6 14:00:18 2017 mstenber
# Edit time:     30 min
#
"""

This is what I consider to be the minimal 'kh-server' in _my_
home. For your home, it may differ. Notably, it contains hooks for all
modules that are _hardware dependant_, and therefore controls
ultimately their state. All clients will manipulate their state
remotely.

"""

import argparse
import logging
import socket

import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.sync as sync
import kodinhenki.updater as updater

is_cer = socket.gethostname() == 'cer'


def start_wemo():
    import kodinhenki.wemo.device_tracker as dt
    ip = None
    if is_cer:
        ip = '192.168.44.1'
        # The remote_ip based lookup does not really seem to work with v4.
        # Oh well. So hardcode here for the cer case with N addresses.

    updater.add(dt.get(ip=ip,
                       remote_ip='192.168.44.254',
                       discovery_port=54321,
                       event_port=8989))


def start():
    import kodinhenki.hue as hue
    import kodinhenki.mpower as mpower
    import kodinhenki.owrt_wifi as _owrt_wifi

    # Start database (implicitly on the hardcoded port + any ip)
    sync.start()

    # Start the devices
    updater.add(hue.get_updater('192.168.44.10'))

    updater.add(mpower.get_updater('192.168.44.21', 'pro'))
    updater.add(mpower.get_updater('192.168.44.20', 'mini'))

    # WeMo is dead, baby!
    # start_wemo()

    if is_cer:
        # We're CER => can check locally wifi state
        _owrt_wifi.start()


def create_shared_argparser(desc):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument('-d', '--debug', action='store_true',
                   help='enable debugging')
    p.add_argument('-l', '--lock', action='store_true',
                   help='debug locks')
    return p


def parse_shared(p):
    args = p.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)-15s %(name)s %(message)s')
    if args.lock:
        _prdb_kh.set_lock_check_enabled(True)
    return args

if __name__ == '__main__':
    start()
