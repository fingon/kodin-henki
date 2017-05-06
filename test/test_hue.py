#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_hue.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2017 Markus Stenberg
#
# Created:       Sat May  6 12:41:36 2017 mstenber
# Last modified: Sat May  6 13:02:41 2017 mstenber
# Edit time:     11 min
#
"""

Test the Hue part of the equation

"""


get_light = '{"1":{"state":{"on":false,"bri":254,"hue":14910,"sat":144,"effect":"none","xy":[0.4596,0.4105],"ct":369,"alert":"select","colormode":"ct","reachable":true},"type":"Extended color light","name":"Living","modelid":"LCT001","manufacturername":"Philips","uniqueid":"00:17:88:01:00:e1:fc:04-0b","swversion":"5.23.1.13452"}}'

get_sensor = '{"1":{"state":{"daylight":null,"lastupdated":"none"},"config":{"on":true,"configured":false,"sunriseoffset":30,"sunsetoffset":-30},"name":"Daylight","type":"Daylight","modelid":"PHDL00","manufacturername":"Philips","swversion":"1.0"},"2":{"state":{"buttonevent":34,"lastupdated":"2017-05-06T07:31:56"},"config":{"on":true},"name":"Tap","type":"ZGPSwitch","modelid":"ZGPSWITCH","manufacturername":"Philips","uniqueid":"00:00:00:00:00:40:2d:7b-f2"},"3":{"state":{"temperature":2162,"lastupdated":"2017-05-06T09:46:56"},"config":{"on":true,"battery":100,"reachable":true,"alert":"none","ledindication":false,"usertest":false,"pending":[]},"name":"Hue temperature sensor 1","type":"ZLLTemperature","modelid":"SML001","manufacturername":"Philips","swversion":"6.1.0.18912","uniqueid":"00:17:88:01:02:03:63:dc-02-0402"},"4":{"state":{"presence":false,"lastupdated":"2017-05-06T08:18:58"},"config":{"on":true,"battery":100,"reachable":true,"alert":"none","ledindication":false,"usertest":false,"sensitivity":2,"sensitivitymax":2,"pending":[]},"name":"BathroomM","type":"ZLLPresence","modelid":"SML001","manufacturername":"Philips","swversion":"6.1.0.18912","uniqueid":"00:17:88:01:02:03:63:dc-02-0406"},"5":{"state":{"lightlevel":0,"dark":true,"daylight":false,"lastupdated":"2017-05-06T09:43:50"},"config":{"on":true,"battery":100,"reachable":true,"alert":"none","tholddark":16000,"tholdoffset":7000,"ledindication":false,"usertest":false,"pending":[]},"name":"Hue ambient light sensor 1","type":"ZLLLightLevel","modelid":"SML001","manufacturername":"Philips","swversion":"6.1.0.18912","uniqueid":"00:17:88:01:02:03:63:dc-02-0400"},"6":{"state":{"status":0,"lastupdated":"2017-05-06T08:48:43"},"config":{"on":true,"reachable":true},"name":"MotionSensor 4.Companion","type":"CLIPGenericStatus","modelid":"PHA_STATE","manufacturername":"Philips","swversion":"1.0","uniqueid":"MotionSensor 4.Companion","recycle":true}}'

import json

import kodinhenki as _kh
import kodinhenki.hue as _hue
import kodinhenki.prdb_kh as _prdb_kh

from mock import patch


def test_hue():
    _kh.get_database()

    def _request(o, mode='GET', address=None, data=None):
        if mode == 'GET' and address == '/api/username/lights/':
            return json.loads(get_light)
        if mode == 'GET' and address == '/api/username/sensors/':
            return json.loads(get_sensor)

        raise NotImplementedError('%s %s %s' % (mode, address, data))

    def _connect(o):
        o.username = 'username'

    with patch('phue.Bridge.request', new=_request),\
            patch('phue.Bridge.connect', new=_connect):
        h = _hue.get_updater('127.0.0.1')
        h.update()
    assert _prdb_kh.HueBulb.get_named('Living').on is False
    # TBD: Test sensor values as well.
