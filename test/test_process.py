#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_process.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Wed Oct  1 15:18:36 2014 mstenber
# Last modified: Mon Oct 27 20:50:56 2014 mstenber
# Edit time:     5 min
#
"""

ensure process monitor works

"""

import kodinhenki as kh
import kodinhenki.process as process
import kodinhenki.prdb_kh as _prdb_kh

def test_process():
    kh.drop_database() # in case previous thing played with it
    db = kh.get_database()
    pm = process.ProcessMonitor({'zsh': 'zsh',
                                 'x': 'dghswaedherh'})
    #assert pm.next_update_in_seconds() < 0 # n/a - always constant
    pm.update()
    assert pm.next_update_in_seconds() > 0
    assert _prdb_kh.Process.get_named('zsh').get('on')
    assert not _prdb_kh.Process.get_named('x').get('on')

