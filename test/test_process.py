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
# Last modified: Sat Oct  4 14:56:33 2014 mstenber
# Edit time:     2 min
#
"""

ensure process monitor works

"""

import kodinhenki as kh
import kodinhenki.process as process

def test_process():
    db = kh.get_database()
    pm = process.ProcessMonitor(db, {'zsh': 'zsh',
                                     'x': 'dghswaedherh'})
    #assert pm.next_update_in_seconds() < 0 # n/a - always constant
    pm.update()
    assert pm.next_update_in_seconds() > 0
    assert db.get('zsh').get('on')
    assert not db.get('x').get('on')
