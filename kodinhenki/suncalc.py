#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: suncalc.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Sat Apr 19 19:21:34 2014 mstenber
# Last modified: Thu Apr 24 21:16:09 2014 mstenber
# Edit time:     77 min
#
"""

Sunrise/sunset calculator

Based on http://williams.best.vwh.net/sunrise_sunset_algorithm.htm

"""

ZENITH_OFFICIAL=90
ZENITH_CIVIL=96
ZENITH_NAUTICAL=102
ZENITH_ASTRONOMICAL=108

ZENITHS=[ZENITH_OFFICIAL, ZENITH_CIVIL, ZENITH_NAUTICAL, ZENITH_ASTRONOMICAL]

ZENITH2NAME={ZENITH_OFFICIAL:'official',
             ZENITH_CIVIL:'civil',
             ZENITH_NAUTICAL:'nautical',
             ZENITH_ASTRONOMICAL:'astronomical'
             }

DEFAULT_LON=25
DEFAULT_LAT=60
DEFAULT_ZENITH=ZENITH_OFFICIAL

import datetime
try:
    from dateutil.tz import tzlocal
except ImportError:
    from tzlocal import get_localzone as tzlocal
import math

def _bound(v, min, max):
    if v < min:
        return _bound(v + (max - min), min, max)
    if v >= max:
        return _bound(v - (max - min), min, max)
    return v

def _boundDegrees(d):
    return _bound(d, 0, 360)

def r2d(r):
    v = r * 180 / math.pi
    #v = _bound(v, 0, 360)
    return v

def d2r(d):
    return d * math.pi / 180

def phase(dt=None, date=None, lon=DEFAULT_LON, lat=DEFAULT_LAT):
    if dt is None:
        dt = datetime.datetime.now(tzlocal())
    if not date:
        date = datetime.date.today()
    # Even at poles should be resolvable in 200d, or math is wrong?
    for i in range(200):
        for i, z in enumerate(reversed(ZENITHS)):
            dt2 = calc(date=date, lon=lon, lat=lat, zenith=z)
            if isinstance(dt2, datetime.datetime) and dt2 > dt:
                return i, z, False, dt2
        for i, z in enumerate(ZENITHS):
            dt2 = calc(date=date, lon=lon, lat=lat, sunset=True, zenith=z)
            if isinstance(dt2, datetime.datetime) and dt2 > dt:
                return i + len(ZENITHS), z, True, dt2
        date = date + datetime.timedelta(days=1)

def within_zenith(**kwargs):
    dt = kwargs.get('dt', None)
    if dt is None:
        dt = datetime.datetime.now(tzlocal())
    dt1 = calc(**kwargs)
    dt2 = calc(sunset=True, **kwargs)
    if isinstance(dt1, datetime.datetime) and dt1 < dt:
        if isinstance(dt2, datetime.datetime) and dt2 > dt:
            return True


def calc(date=None, lon=DEFAULT_LON, lat=DEFAULT_LAT,
         sunset=False, zenith=DEFAULT_ZENITH):
    if not date:
        date = datetime.date.today()

    # 1. date of year
    n1 = math.floor(275 * date.month / 9)
    n2 = math.floor((date.month + 9) / 12)
    n3 = 1 + math.floor((date.year - 4 * math.floor(date.year / 4) + 2) / 3)
    n = n1 - n2 * n3 + date.day - 30
    #print 'n', n

    # 2. longitude => hour value => approximate time
    lngHour = lon / 15.0
    if not sunset:
        t = n + ((6 - lngHour) / 24)
    else:
        t = n + ((18 - lngHour) / 24)
    #print 't', t

    # 3. Sun's mean anomaly
    m = 0.9856 * t - 3.289
    #print 'm', m

    # 4. Sun's right true longitude
    l = m + 1.916 * math.sin(d2r(m)) + 0.02 * math.sin(d2r(2 * m)) + 282.634
    l = _boundDegrees(l)
    #print 'l', l

    # 5a Sun's right ascension
    ra = r2d(math.atan(0.91764 * math.tan(d2r(l))))
    ra = _boundDegrees(ra)
    #print 'ra', ra

    # 5b RA value needs to be in same quadrant as L
    lq = math.floor(l / 90) * 90
    raq = math.floor(ra / 90) * 90
    ra = ra + (lq - raq)

    # 5c RA as hours
    ra = ra / 15

    # 6 calculate Sun's declination
    sinDec = 0.39782 * math.sin(d2r(l))
    cosDec = math.cos(math.asin(sinDec))

    # 7a Calculate the Sun's local hour angle
    cosH = math.cos(d2r(zenith)) - sinDec * math.sin(d2r(lat)) / \
    (cosDec * math.cos(d2r(lat)))
    if cosH > 1:
        return sunset
    if cosH < -1:
        return not sunset

    # 7b finish calculating H and convert into hours
    if not sunset:
        h = 360 - r2d(math.acos(cosH))
    else:
        h = r2d(math.acos(cosH))
    h = h / 15

    # 8 calculate local mean time of rising/setting
    t = h + ra - 0.06571 * t - 6.622

    # adjust back to UTC
    ut = t - lngHour
    ut = _bound(ut, 0, 24)

    # .. and return as UTC for the time being
    import pytz
    dt = datetime.datetime(date.year, date.month, date.day,
                           tzinfo=pytz.timezone('UTC'))
    dt = dt + datetime.timedelta(hours=ut)
    return dt.astimezone(tzlocal())


if __name__ == '__main__':
    # Now
    for i, z in enumerate(reversed(ZENITHS)):
        print(i, z, False, calc(sunset=False, zenith=z))
    for i, z in enumerate(ZENITHS):
        print(i, z, True, calc(sunset=True, zenith=z))
    print(phase())

    print('.. dates')
    # Midsummer
    d1 = datetime.date(2014, 6, 22)
    print(calc(date=d1, sunset=False))
    print(calc(date=d1, sunset=True))
    # Christmas
    d2 = datetime.date(2014, 12, 24)
    print(calc(date=d2, sunset=False))
    print(calc(date=d2, sunset=True))

    print('.. at 0 long')
    print(calc(lat=0, sunset=False))
    print(calc(lat=0, sunset=True))
    print('.. at north pole')
    print(calc(lat=88, sunset=False))
    print(calc(lat=88, sunset=True))
    print(phase(lat=88))
    print('.. at south pole')
    print(calc(lat=-88, sunset=False))
    print(calc(lat=-88, sunset=True))
    print(phase(lat=-88))

    print(within_zenith())
