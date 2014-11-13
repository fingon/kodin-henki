#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: webcam_light.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Tue Nov 11 16:07:59 2014 mstenber
# Last modified: Thu Nov 13 14:03:21 2014 mstenber
# Edit time:     18 min
#
"""

This is OpenCV (http://opencv.org) using module that grabs pictures
from webcam, and considers the _median_ brightness of
pixels. Assumption is that _most_ of the picture is ambient background
-> the darker it is, the worse the ambient light is.

This is useful in e.g. Finland, where daytime (given sufficient cloud
cover) may still be too dark :-p

Brightness formula:

https://social.msdn.microsoft.com/Forums/en-US/4e53a3c8-97c4-4560-9aae-bcc8609951d2/reading-light-values-from-webcam-to-simulate-light-sensor-use-colorbrightness-average?forum=roboticssimulation

Note: Instead of the classic 'on' field, the WebCam based light sensor
has two flags:

'enabled'

and

'brightness'

(and built-in update interval)

TBD: Some day it would be nice to actually have real control over
webcam (=> no auto-gain that neccessitates this logic), or
alternatively noise-based detection of how dark the place is..

"""

import cv2
import numpy
import prdb

import kodinhenki.updater as _updater

def get_image():
    vc = cv2.VideoCapture()
    if vc.open(0):
        retval, image = vc.retrieve()
        vc.release()
        if retval is True:
            return image

def get_brightness():
    image = get_image()
    if image is None:
        return
    # Convert the (x, y, (r,g,b) to simply list of (r,g,b)
    pixels = image.shape[0] * image.shape[1]
    assert len(image.shape) == 3 and image.shape[2] == 3
    image.reshape(pixels, 3)
    b = numpy.median(numpy.inner(image, numpy.array([0.299, 0.587, 0.114])))
    return b

class WebCamMonitor(prdb.Owner, _updater.Updated):
    pass

def start():
    pass

if __name__ == '__main__':
    import time
    while True:
        print get_brightness()
        time.sleep(1)
