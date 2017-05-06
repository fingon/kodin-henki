#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: mpower.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2017 Markus Stenberg
#
# Created:       Sat May  6 12:06:25 2017 mstenber
# Last modified: Sat May  6 14:01:19 2017 mstenber
# Edit time:     34 min
#
"""MPower module.

Supports:

- gathering binary on/off signal (that can be used as sensor)
- setting on/off signal (to toggle the relay on and off)

TBD: Eventually, it would be nice to gather energy statistics this way
too. Possibly. Or figure some other way to do the same (perhaps on the
device?).

"""

import json

import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.updater as _updater

import prdb

CREDENTIALS = 'username=ubnt&password=ubnt'
SESSION_ID = '12345678901234567890123456789012'


class MPower(prdb.Owner):

    def object_changed(self, **kwargs):
        self.updater.plug_changed(self, **kwargs)

_prdb_kh.MPower.set_create_owner_instance_callback(MPower)


def request(method, url, data=None):
    import urllib2
    import urllib

    class NoRedirectHandler(urllib2.HTTPRedirectHandler):

        def http_error_302(self, req, fp, code, msg, headers):
            infourl = urllib.addinfourl(fp, headers, req.get_full_url())
            infourl.status = code
            infourl.code = code
            return infourl
        http_error_300 = http_error_302
        http_error_301 = http_error_302
        http_error_303 = http_error_302
        http_error_307 = http_error_302

    print('xxx', method, url, data)
    opener = urllib2.build_opener(NoRedirectHandler())
    request = urllib2.Request('http://%s' % url, data=data)
    request.add_header('Cookie', 'AIROS_SESSIONID=%s' % SESSION_ID)
    request.get_method = lambda: method
    f = opener.open(request)
    return f.read()


class MPowerUpdater(prdb.Owner, _updater.IntervalUpdated):
    update_interval = 30

    default_on_threshold = 1
    on_threshold_by_port = {}

    def plug_changed(self, b, key, new, by, **kwargs):
        if key != 'output':
            return
        self.request('PUT', 'sensors/%d' % b.port,
                     'output=%d' % (1 if new else 0))
        self.mark_dirty()

    def request(self, method, url, expect_result=True):
        full_url = '%s/%s' % (self.ip, url)
        for i in range(2):
            s = request(method, full_url)
            if s or not expect_result:
                break
            elif i:
                raise Exception('Unable to access %s' % full_url)
            request('POST', '%s/login.cgi' % self.ip, CREDENTIALS)
        if s:
            return json.loads(s)

    def update_in_timer(self):
        r = self.request('GET', 'sensors')
        assert r
        r = r['sensors']
        for o in r:
            port = o['port']
            power = o['power']
            output = o['output']
            output = True if output else False
            need_power = self.on_threshold_by_port.get(
                port, self.default_on_threshold)
            is_on = True if power >= need_power else False
            name = '%s_%d' % (self.name, port)
            o = _prdb_kh.MPower.new_named(
                name, on=is_on, output=output).get_owner()
            o.port = port
            o.updater = self

_prdb_kh.MPowerUpdater.set_create_owner_instance_callback(MPowerUpdater)


def get_updater(ip, name, default_on_threshold=1, on_threshold_by_port={},
                **kwargs):
    assert ip
    o = _prdb_kh.MPowerUpdater.new_named(name, **kwargs).get_owner()
    o.name = name
    o.ip = ip
    o.default_on_threshold = default_on_threshold
    o.on_threshold_by_port = on_threshold_by_port
    return o
