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
# Last modified: Wed Oct  1 15:23:02 2014 mstenber
# Edit time:     2 min
#
"""

ensure process monitor works

"""

import kodinhenki.db as db
import kodinhenki.process as process

def test_process():
    pm = process.ProcessMonitor({'zsh': 'zsh',
                                 'x': 'dghswaedherh'})
    pm.update()
    assert db.get_database().get('zsh').get('on')
    assert not db.get_database().get('x').get('on')
