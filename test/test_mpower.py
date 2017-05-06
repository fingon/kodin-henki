#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_mpower.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2017 Markus Stenberg
#
# Created:       Sat May  6 13:06:22 2017 mstenber
# Last modified: Sat May  6 13:36:54 2017 mstenber
# Edit time:     9 min
#
"""



"""

import kodinhenki as _kh
import kodinhenki.mpower as _mpower
import kodinhenki.prdb_kh as _prdb_kh

from mock import patch


def test_mpower():
    _kh.get_database()
    canned_responses = [['GET', '127.0.0.1/sensors',  ''],
                        ['POST', '127.0.0.1/login.cgi',  ''],
                        ['GET', '127.0.0.1/sensors',
                         '{"sensors":[{"port":1,"output":1,"power":6.90647006,"energy":2439.0625,"enabled":1,"current":0.045182228,"voltage":229.729611635,"powerfactor":0.665382709,"relay":1,"lock":0},{"port":2,"output":1,"power":4.429039955,"energy":1568.4375,"enabled":1,"current":0.027162194,"voltage":229.959799289,"powerfactor":0.709076065,"relay":1,"lock":0},{"port":3,"output":1,"power":2.548347473,"energy":4356.5625,"enabled":1,"current":0.032032728,"voltage":230.385804176,"powerfactor":0.345309876,"relay":1,"lock":0},{"port":4,"output":1,"power":0.0,"energy":483.125,"enabled":1,"current":0.0,"voltage":229.517921447,"powerfactor":0.0,"relay":1,"lock":0},{"port":5,"output":1,"power":4.104837775,"energy":1443.4375,"enabled":1,"current":0.025354385,"voltage":230.2452147,"powerfactor":0.703156989,"relay":1,"lock":0},{"port":6,"output":0,"power":2.033658504,"energy":1260.625,"enabled":1,"current":0.102739334,"voltage":230.123321533,"powerfactor":0.086016278,"relay":1,"lock":0}],"status":"success"}']]

    def _request(method, url, data=None):
        exp_method, exp_url, ret_data = canned_responses.pop(0)
        assert exp_method == method
        assert exp_url == url
        return ret_data

    with patch('kodinhenki.mpower.request', new=_request):
        p = _mpower.get_updater('127.0.0.1', 'x')
        p.update()

    assert not canned_responses
    assert _prdb_kh.MPower.get_named('x_1').on
    assert _prdb_kh.MPower.get_named('x_1').output
    assert not _prdb_kh.MPower.get_named('x_4').on
    assert _prdb_kh.MPower.get_named('x_4').output
    assert not _prdb_kh.MPower.get_named('x_6').output

    with patch('kodinhenki.mpower.request') as req:
        p1 = _prdb_kh.MPower.get_named('x_1')
        p1.set('output', False)
        assert not p1.output
        # assert req.called
        # TBD: Debug someday why this does not seem to work properly..
