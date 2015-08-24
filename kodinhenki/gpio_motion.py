#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: gpio_motion.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2015 Markus Stenberg
#
# Created:       Mon Aug 24 10:46:36 2015 mstenber
# Last modified: Mon Aug 24 11:22:18 2015 mstenber
# Edit time:     13 min
#
"""

GPIO-based motion detector.

Assumption: You have something (e.g. HC-SR501) that shows it's value
as GPIO, and your device (e.g. Pi) is configured like this:

echo 8 > /sys/class/gpio/export
echo in > /sys/class/gpio/gpio8/direction
echo both > /sys/class/gpio/gpio8/edge

=> No-poll motion sensing, here we come!

"""

GPIO='/sys/class/gpio/gpio8/value'

import kodinhenki.prdb_kh as _prdb_kh

import os
import select
import threading

class MotionSensor:
    def __init__(self, name, gpio=8):
        self.o = _prdb_kh.MotionSensor.new_named(name)
        self.path = '/sys/class/gpio/gpio%d/value' % gpio
        self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
    def get_value(self):
        #f.seek(0)
        os.lseek(self.fd, 0, os.SEEK_SET)
        s = os.read(self.fd, 1024)
        s = int(s.strip())
        return s
    def loop(self):
        p = select.poll()
        p.register(self.fd, select.POLLPRI)
        while True:
            v = self.get_value()
            with _prdb_kh.lock:
                v = v and True or False
                self.o.on = v
            r = p.poll()

def start(name, **kw):
    ms = MotionSensor(name, **kw)
    t = threading.Thread(target=ms.loop)
    t.daemon = True
    t.start()
    return dict(t=t, ms=ms)

if __name__ == '__main__':
    import kodinhenki
    kodinhenki.get_database()
    ms = MotionSensor('ms')
    print(ms.get_value())

