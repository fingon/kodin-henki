#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: test_db.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 14:53:31 2014 mstenber
# Last modified: Mon Sep 22 15:10:28 2014 mstenber
# Edit time:     6 min
#
"""

Some tests for the db module

"""

import unittest
import kodinhenki

class Basic(unittest.TestCase):
    def test_base(self):
        db1 = kodinhenki.getDatabase()
        assert db1
        db2 = kodinhenki.getDatabase()
        assert db1 is db2

    def test_o(self):
        d = kodinhenki.getDatabase()
        d.add(name='foo', key='value')

if __name__ == '__main__':
    unittest.main()
