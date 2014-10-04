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
# Last modified: Sat Oct  4 12:50:58 2014 mstenber
# Edit time:     6 min
#
"""

This is what I consider to be the minimal 'kh-server' in _my_
home. For your home, it may differ. Notably, it contains hooks for all
modules that are _hardware dependant_, and therefore controls
ultimately their state. All clients will manipulate their state
remotely.

"""

import logging
logging.basicConfig(level=logging.DEBUG)

import kodinhenki.hue as hue
import kodinhenki.wemo as wemo
import kodinhenki.sync as sync
import kodinhenki.updater as updater

# Start database (implicitly on the hardcoded port + any ip)
sync.start_server()

# Start the devices
updater.add(hue.get(ip='192.168.44.10'))
updater.add(wemo.get(remote_ip='192.168.44.254',
                     discovery_port=54321,
                     event_port=8989))
