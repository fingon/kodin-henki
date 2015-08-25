#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: poro-start.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Created:       Sun Jun  1 22:44:30 2014 mstenber
# Last modified: Tue Aug 25 10:06:46 2015 mstenber
# Edit time:     21 min
#
"""

poro-specific remote agent that provides just look at whether user is
idle on the computer + what's going on with the projector software.

"""

import khserver

import kodinhenki as kh
import kodinhenki.process as process
import kodinhenki.user_active as user_active
import kodinhenki.sync as sync
import kodinhenki.prdb_kh as _prdb_kh
import os

def _monitor_off():
    os.system('pmset displaysleepnow')

def _itunes_pause():
    os.system('osascript "/Users/mstenber/Library/Scripts/itunes pause.scpt"')

def _set_volume(n):
    os.system('osascript -e "set Volume %d"' % n)

def start():
    process.start({#'xbmc': 'XBMC.app/Contents',
                   'kodi': 'Kodi.app/Contents',
                   'emacs': 'Emacs.app/Contents'})
    user_active.start('poro')
    def _f(o, key, old, new, **kwargs):
        if o.id == '.kh.home.' and key == 'state_name':
            if old == 'ProjectorState':
                _set_volume(3)
            # TimeoutState is bit questionable..
            # it is the 'default' if e.g. poro is not connected,
            # so do nothing there for now.
            if new == 'NightState':
                _monitor_off()
                #_itunes_pause()
                # Hmm. Good idea? Maybe not, if listening to stuff on bed.
            elif new == 'AwayState':
                _monitor_off()
                _itunes_pause()
            elif new == 'ProjectorState':
                # Further away from computer -> more volume
                _set_volume(10)
                _itunes_pause()

    kh.get_database().object_changed.connect(_f)

if __name__ == '__main__':
    p = khserver.create_shared_argparser('poroserver')
    args = khserver.parse_shared(p)
    with _prdb_kh.lock:
        sync.start()
        start()

# XXX - do clever things with set_volume, itunes_pause, etc..

