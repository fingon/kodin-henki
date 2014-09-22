kodin-henki
===========

'Spirit of home' - my home automation project based on Python 2.

Notably influenced by https://github.com/balloob/home-assistant - however,
as I am not that keen on Python 3, and some design choices there, I figured
rolling my own would be easiest (cough).

What does it contain?
=====================

* (Python-encoded) state machine mechanism
* Some utility 'actions' on OS X and various embedded devices to perform
  things state machine dictates should be done
* Multi-machine support (client-server, with same API available at both
  ends; clients can be also non-Python)
* Minimalist sun state calculator

Code characteristics
====================

* Support for Python 2.6+ (and perhaps Python 3)
* Pure Python solution (so that it runs easily e.g. on OpenWrt without
  python-dev or equivalent)
* Correctness - should be robust. Ensured by reasonable unit test coverage
  (and potentially system tests later on)

Requirements
============

* For Philips Hue support, phue (optional) 
* TBD - Belkin WeMo backend 
* tox (optional, for unit testing)


Design
======

As simple as possible - basically, simple signal mechanism (without
external dependencies as e.g. pysignal is not really maintained), combined
with use of threading where applicable. Integration of third-party
libraries to single-threaded application is too painful so I cannot be
bothered.

Non-goals
=========

* 'efficiency'

