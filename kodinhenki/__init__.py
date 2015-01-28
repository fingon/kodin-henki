#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: __init__.py $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2014 Markus Stenberg
#
# Created:       Mon Sep 22 15:05:48 2014 mstenber
# Last modified: Wed Jan 28 22:03:46 2015 mstenber
# Edit time:     11 min
#
"""

By default, we operate in in-memory mode..

"""


PORT=31342

_db = None

import prdb
import kodinhenki.prdb_kh as _prdb_kh

import logging
logger = logging.getLogger(__name__)
_debug = logger.debug

def get_database():
    global _db
    if _db is not None:
        return _db
    # Autocommit = _Every_ single set implies also commit.
    # Not very effective, but we do not really care about efficiency
    # here as much as correctness, and hey, it is in-memory after all..
    _db = prdb.new(autocommit=True)
    _db.add_app(_prdb_kh.KH)
    _db.check_schema()
    _debug('created new database %s', _db)
    return _db

def drop_database():
    global _db
    if _db is None:
        return
    _debug('dropped database %s', _db)
    _prdb_kh.KH.parent = None
    _db = None

