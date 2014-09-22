#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: poro-start.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Created:       Sun Jun  1 22:44:30 2014 mstenber
# Last modified: Mon Sep 22 18:04:27 2014 mstenber
# Edit time:     5 min
#
"""

poro-specific remote agent that provides just look at whether user is
idle on the computer + what's going on with the projector software.

"""

import homeassistant.remote as remote
import configparser

config = configparser.ConfigParser()
config.read('poro.conf')

password = config.get('http', 'api_password')
remote_api = remote.API('192.168.42.2', password)

hass = remote.HomeAssistant(remote_api)

import homeassistant.components.process as process
processes = dict(config.items('process'))
process.setup(hass, processes)

import homeassistant.components.user_active as ua
ua.setup(hass, 'poro')

def _monitor_off():
    os.system('pmset displaysleepnow')

def _set_volume(n):
    os.system('osascript -e "set Volume %d"' % n)

def _itunes_pause():
    os.system('osascript "/Users/mstenber/Library/Scripts/itunes pause.scpt"')



hass.start()
hass.block_till_stopped()
