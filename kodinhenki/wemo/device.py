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
# Last modified: Mon Oct 27 22:29:03 2014 mstenber
# Edit time:     58 min
#
"""

Wrapper for functionality of a single device (whether Motion or
Switch, smirk).

"""

import prdb
import kodinhenki.prdb_kh as _prdb_kh
import kodinhenki.wemo as _wemo
import kodinhenki.wemo.service
from kodinhenki.util import Signal

import socket

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

class WemoBase(prdb.Owner):
    _subscription = None # Event subscription, handled externally
    ip = None
    def is_on(self):
        return self.o.get('on')
    def set_services(self, services):
        self.services = services
    def set_url(self, url):
        self.url = url
        p = _parse.urlparse(url)
        ip = p.netloc.split(':')[0]
        self.ip = ip
    def object_changed(self, key, old, new, by, **kwargs):
        if not (key == 'on' and by != _wemo.BY):
            return
        if not self.set_state(new):
            # Do inverse set - back to old value.
            self.o.set(key, old, by=_wemo.BY)


class WemoSwitch(WemoBase):
    def set_state(self, v):
        s = v and '1' or '0'
        return self.services['basicevent'].SetBinaryState(BinaryState=s)
    def turn_on(self):
        self.set('on', True)
    def turn_off(self):
        self.set('on', False)

_prdb_kh.WemoSwitch.set_create_owner_instance_callback(WemoSwitch)

class WemoMotion(WemoBase):
    def set_state(self, v):
        pass

_prdb_kh.WemoMotion.set_create_owner_instance_callback(WemoMotion)

udn_prefix_to_class = [
    ('uuid:Sensor', _prdb_kh.WemoMotion),
    ('uuid:Socket', _prdb_kh.WemoSwitch)
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

def _from_url_string(url, data):
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
    o = cls.get_named(name)
    if o:
        o = o.get_owner()
        if o.url == url:
            return o
    sol = list(doc.getElementsByTagName('service'))
    services = list([
            kodinhenki.wemo.service.from_url_object(url, o2)
            for o2 in sol])
    services = dict([(s.service_type.split(':')[-2].lower(), s) for s in services])
    is_new = False
    if not o:
        o = cls.new_named(name).get_owner()
        is_new = True
    o.set_url(url)
    o.set_services(services)
    if is_new:
        device_added(o=o)
    return o

def from_url(url):
    try:
        data = urlopen(url, None, 5).read()
    except:
        return
    return _from_url_string(url, data)


