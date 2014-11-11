#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: prdb_kh.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Oct 27 18:00:17 2014 mstenber
# Last modified: Tue Nov 11 16:46:51 2014 mstenber
# Edit time:     8 min
#
"""

Kodinhenki schema declaration for prdb

"""

import prdb

KH = prdb.App('kh', version=1)

HueBulb = KH.declare_class('hue')

HueUpdater = KH.declare_class('hue_updater')

WemoTracker = KH.declare_class('wemo_tracker')

WemoSwitch = KH.declare_class('wemo_switch')
WemoMotion = KH.declare_class('wemo_motion')

Process = KH.declare_class('process')

Home = KH.declare_class('home')

UserActive = KH.declare_class('user_active')

WifiDevice = KH.declare_class('wifi')

WebCamAmbientLight = KH.declare_class('webcam_light')
