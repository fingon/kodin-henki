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
# Last modified: Tue Sep 30 09:17:03 2014 mstenber
# Edit time:     36 min
#
"""

Wrapper for functionality of a single device (whether Motion or
Switch, smirk).

"""

import kodinhenki.db
import kodinhenki.wemo.service
from kodinhenki.util import Signal

import kodinhenki.compat as compat
urlopen = compat.get_urllib_request().urlopen
_parse = compat.get_urllib_parse()

# we could use this, but why bother?
#bd_ns = 'urn:Belkin:device-1-0'

from xml.dom.minidom import parseString

import logging
_debug = logging.debug
_error = logging.error

DEVICE_NAME='wemo.%s'

device_added = Signal()

class WemoBase(kodinhenki.db.Object):
    def __init__(self, url, services, **kwargs):
        self.url = url
        p = _parse.urlparse(url)
        self.ip = p.netloc.split(':')[0]
        self.services = services
        kodinhenki.db.Object.__init__(self, **kwargs)

class WemoSwitch(WemoBase):
    def set_state(self, v):
        raise NotImplementedError

class WemoMotion(WemoBase):
    def set_state(self, v):
        pass

udn_prefix_to_class = [
    ('uuid:Sensor', WemoMotion),
    ('uuid:Socket', WemoSwitch)
    ]

def _get_text_l(l):
    rc = []
    for node in l:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def _wemo_string(o, n, default=None):
    l = o.getElementsByTagName(n)
    if l:
        s = _get_text_l(l[0].childNodes)
        if s:
            return s
    return default

def _from_db_url_string(db, url, data):
    doc = parseString(data)
    assert doc
    #_debug('got device: %s' % repr(doc))
    udn = _wemo_string(doc, 'UDN')
    if not udn:
        _debug(' no UDN')
        return
    for prefix, cls in udn_prefix_to_class:
        if udn.startswith(prefix):
            break
    else:
        _debug(' no UDN match:%s' % udn)
        return
    name = _wemo_string(doc, 'friendlyName', '?')
    fname = DEVICE_NAME % name
    try:
        o = db.get(fname)
        assert isinstance(o, cls)
        _debug('%s already existed and is of class %s' % (fname, repr(cls)))
    except KeyError:
        sol = list(doc.getElementsByTagName('service'))
        services = list([
            kodinhenki.wemo.service.from_url_object(url, o2)
            for o2 in sol])
        services = dict([(s.service_type.split(':')[-2].lower(), s) for s in services])
        #_debug('%s enumerated %s => %s' % (name, sol, services))
        o = cls(name=fname, url=url, services=services)
        db.add_object(o)
        device_added(o=o)
    return o

def from_db_url(db, url):
        data = urlopen(url).read()
        #_debug('got data: %s' % repr(data))
        return _from_db_url_string(db, url, data)


