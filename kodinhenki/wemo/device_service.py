#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: device_service.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Sat Sep 27 18:14:32 2014 mstenber
# Last modified: Sat Sep 27 20:31:54 2014 mstenber
# Edit time:     41 min
#
"""

Single service for a device. Probably should not be stored in a
database, just used locally. Bootstrapped from (part of) root device
service specification.

It wraps SOAP ugliness behind Python facade.

"""

import kodinhenki.wemo.device

from xml.dom.minidom import parseString

import kodinhenki.compat as compat
urllib_request = compat.get_urllib_request()
urlopen = urllib_request.urlopen
urljoin = compat.get_urllib_parse().urljoin

import logging
_debug = logging.debug
_error = logging.error

s_ns = 'urn:Belkin:service-1-0'
soap_ns = 'http://schemas.xmlsoap.org/soap/envelope/'

def _e_children(n):
    return [n for n in n.childNodes if n.nodeType == n.ELEMENT_NODE]
def _unique_e_child(n):
    l = list(_e_children(n))
    assert len(l) == 1
    return l[0]

class Action:
    def __init__(self, service, name):
        self.service = service
        self.name = name
        self.url = urljoin(service.url, service.control_url)
    def __call__(self, **kwargs):
        service = self.service.service_type
        action = self.name
        argl = ['<%s>%s</%s>' % (k, v, k) for (k, v) in kwargs.items()]
        args = ''.join(argl)
        data = '''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <s:%(action)s xmlns:s="%(service)s">
      %(args)s
    </s:%(action)s>
  </soap:Body>
</soap:Envelope>''' % locals()
        headers = {'SOAPAction': '"%s#%s"' % (service, action),
        'Content-Type': 'text/xml'}
        _debug('url:%s - headers:%s - data:%s' % (self.url, headers, data))
        req = urllib_request.Request(self.url, data.encode('utf-8'), headers)
        data = urlopen(req).read()
        doc = parseString(data)
        # Doc contains Envelope + Body + X + then inside that, key = value
        bl = doc.getElementsByTagNameNS(soap_ns, 'Body')
        assert len(bl) >= 1
        b = bl[0]

        r = _unique_e_child(b)

        rh = {}
        for e in _e_children(r):
            rh[e.localName] = kodinhenki.wemo.device._get_text_l(e.childNodes)
        return rh

class Service:
    populated = False
    def __init__(self, url, scdp, **kwargs):
        self.url = url
        self.scdp = scdp
        self.__dict__.update(kwargs)
    def populate(self):
        if self.populated: return
        self.populated = True
        assert self.scdp
        nurl = urljoin(self.url, self.scdp)
        data = urlopen(nurl).read()
        #_debug('got sdata: %s' % repr(data))
        doc = parseString(data)
        assert doc
        _wemo_string = kodinhenki.wemo.device._wemo_string
        for al in doc.getElementsByTagName('actionList'):
            for a in al.getElementsByTagName('action'):
                n = _wemo_string(a, 'name')
                setattr(self, n, Action(self, n))
    def __getattr__(self, x):
        if not self.populated:
            self.populate()
            # Retry default behavior, perhaps we won't wind up here again
            return getattr(self, x)
        else:
            raise AttributeError()

def from_url_object(url, o):
    _wemo_string = kodinhenki.wemo.device._wemo_string
    return Service(url=url,
                   service_type=_wemo_string(o, 'serviceType'),
                   control_url=_wemo_string(o, 'controlURL'),
                   event_sub_url=_wemo_string(o, 'eventSubURL'),
                   scdp=_wemo_string(o, 'SCPDURL'))

