#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: device.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Sat Sep 27 17:55:50 2014 mstenber
# Last modified: Sat Sep 27 18:48:38 2014 mstenber
# Edit time:     18 min
#
"""

Wrapper for functionality of a single device (whether Motion or
Switch, smirk).

"""

import kodinhenki.db
import kodinhenki.wemo.device_service
import kodinhenki.compat as compat
urlopen = compat.get_urllib_request().urlopen

bd_ns = 'urn:Belkin:device-1-0'
from xml.dom.minidom import parseString

import logging
_debug = logging.debug
_error = logging.error

DEVICE_NAME='wemo.%s'

_parent = kodinhenki.db.Object

class WemoSwitch(_parent):
    def set_state(self, v):
        raise NotImplementedError

class WemoMotion(_parent):
    def set_state(self, v):
        pass

udn_prefix_to_class = [
    ('uuid:Sensor', WemoMotion),
    ('uuid:Switch', WemoSwitch)
    ]

def _get_text_l(l):
    rc = []
    for node in l:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def _wemo_string(o, n, default=None):
    l = o.getElementsByTagNameNS(bd_ns, n)
    if l:
        s = _get_text_l(l[0].childNodes)
        if s:
            return s
    return default


def _from_db_url_string(db, url, data):
    doc = parseString(data)
    _debug('got device: %s' % repr(doc))
    udn = _wemo_string(doc, 'UDN')
    if not udn:
        return
    for prefix, cls in udn_prefix_to_class:
        if udn.startswith(prefix):
            break
    else:
        return
    name = _wemo_string(doc, 'friendlyName', '?')
    fname = DEVICE_NAME % name
    try:
        o = db.get(fname)
        assert isinstance(o, cls)
    except KeyError:
        services = list([
            kodinhenki.wemo.device_service.from_url_object(url, o2)
            for o2 in doc.getElementsByTagNameNS(bd_ns, 'service')])
        o = cls(name=fname, url=url, services=services)
        db.add_object(o)
    return o

def from_db_url(db, url):
        data = urlopen(url).read()
        _debug('got data: %s' % repr(data))
        return _from_db_url_string(db, url, data)


