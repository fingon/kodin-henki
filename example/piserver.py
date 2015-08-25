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
# Last modified: Tue Aug 25 10:07:55 2015 mstenber
# Edit time:     6 min
#
"""

"""

import khserver
import kodinhenki.sync as sync
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.bh1750fvi_light as _light
import kodinhenki.gpio_motion as _motion

def start():
    _light.start('corridor')
    _motion.start('corridor')

if __name__ == '__main__':
    p = khserver.create_shared_argparser('piserver')
    args = khserver.parse_shared(p)
    with _prdb_kh.lock:
        s = sync.start(if_list=['wlan0'])
        #s['p']. TBD: set keep-alive interval to ~1? :p
        start()

