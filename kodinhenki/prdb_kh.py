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
# Last modified: Mon Oct 27 21:07:58 2014 mstenber
# Edit time:     4 min
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
