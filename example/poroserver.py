#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: poro-start.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Created:       Sun Jun  1 22:44:30 2014 mstenber
# Last modified: Sat Oct  4 15:18:07 2014 mstenber
# Edit time:     8 min
#
"""

poro-specific remote agent that provides just look at whether user is
idle on the computer + what's going on with the projector software.

"""

import logging
logging.basicConfig(level=logging.DEBUG)

import kodinhenki as kh
import kodinhenki.process as process
import kodinhenki.user_active as user_active
import kodinhenki.sync as sync
import os

def start():
    process.start({'process.xbmc': 'XBMC', 'process.emacs': 'Emacs.app'})
    user_active.start('user_active.poro')

if __name__ == '__main__':
    ip = os.environ.get('KHIP', '192.168.42.1')
    db = kh.get_database()
    sync.start_client(db, (ip, kh.PORT))
    start()

# XXX - do clever things with set_volume, itunes_pause, etc..

def _monitor_off():
    os.system('pmset displaysleepnow')

def _set_volume(n):
    os.system('osascript -e "set Volume %d"' % n)

def _itunes_pause():
    os.system('osascript "/Users/mstenber/Library/Scripts/itunes pause.scpt"')
