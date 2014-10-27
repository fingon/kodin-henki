#!/usr/bin/env python3.4
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
# Last modified: Mon Oct 27 21:33:39 2014 mstenber
# Edit time:     12 min
#
"""

This is what I consider to be the minimal 'kh-server' in _my_
home. For your home, it may differ. Notably, it contains hooks for all
modules that are _hardware dependant_, and therefore controls
ultimately their state. All clients will manipulate their state
remotely.

"""

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(message)s')
logging.getLogger('kh.updater').setLevel(logging.INFO)

import kodinhenki.hue as hue
import kodinhenki.wemo.device_tracker as dt
import kodinhenki.sync as sync
import kodinhenki.updater as updater

ip=None
import socket

if socket.gethostname() == 'cer':
    ip='192.168.44.1'
    # The remote_ip based lookup does not really seem to work with v4.
    # Oh well. So hardcode here for the cer case with N addresses.

def start():
    # Start database (implicitly on the hardcoded port + any ip)
    sync.start_server()

    # Start the devices
    updater.add(hue.get_updater(ip='192.168.44.10'))
    updater.add(dt.get(ip=ip,
                       remote_ip='192.168.44.254',
                       discovery_port=54321,
                       event_port=8989))

if __name__ == '__main__':
    start()

