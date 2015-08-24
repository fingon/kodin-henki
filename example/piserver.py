#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: piserver.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2015 Markus Stenberg
#
# Created:       Mon Aug 24 10:56:12 2015 mstenber
# Last modified: Mon Aug 24 11:09:00 2015 mstenber
# Edit time:     4 min
#
"""

"""

import kodinhenki.sync as sync
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.bh1750fvi_light as _light
import kodinhenki.gpio_motion as _motion

import logging
logging.basicConfig(level=logging.DEBUG)


def start():
    _light.start('corridor')
    _motion.start('corridor')

if __name__ == '__main__':
    _prdb_kh.set_lock_check_enabled(True)
    with _prdb_kh.lock:
        s = sync.start(if_list=['wlan0'])
        #s['p']. TBD: set keep-alive interval to ~1? :p
        start()

