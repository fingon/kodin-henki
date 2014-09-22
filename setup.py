#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: setup.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 15:01:42 2014 mstenber
# Last modified: Mon Sep 22 15:04:40 2014 mstenber
# Edit time:     2 min
#
"""

Minimalist setup.py

"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='kodinhenki',
      version='0.0.1', # XXXX
      author = 'Markus Stenberg',
      author_email = 'fingon+kh@iki.fi',
      packages = ['kodinhenki']
      )

