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
# Last modified: Sat Sep 27 18:47:29 2014 mstenber
# Edit time:     8 min
#
"""

Single service for a device. Probably should not be stored in a
database, just used locally. Bootstrapped from (part of) root device
service specification.

It wraps SOAP ugliness behind Python facade.

"""

import kodinhenki.wemo.device
import kodinhenki.compat as compat
urlopen = compat.get_urllib_request().urlopen
urljoin = compat.get_urllib_parse().urljoin

import logging
_debug = logging.debug
_error = logging.error

class Service:
    def __init__(self, url, scdp, **kwargs):
        self.url = url
        self.scdp = scdp
        self.__dict__.update(kwargs)
        assert scdp
        nurl = urljoin(url, scdp)
        data = urlopen(nurl).read()
        _debug('got sdata: %s' % repr(data))


def from_url_object(url, o):
    _wemo_string = kodinhenki.wemo.device._wemo_string
    return Service(url=url,
                   service_type=_wemo_string(o, 'serviceType'),
                   control=_wemo_string(o, 'controlURL'),
                   event_sub=_wemo_string(o, 'eventSubURL'),
                   scdp=_wemo_string(o, 'SCPDURL'))

