kodin-henki
===========

'Spirit of home' - my home automation project based on Python 2/3.

Notably influenced by https://github.com/balloob/home-assistant - however,
as I am not that keen on forcing use of Python 3, and some design choices
there, I figured rolling my own would be easiest (cough).

What does it contain?
=====================

* (Python-encoded) state machine mechanism
* Some utility 'actions' on OS X and various embedded devices to perform
  things state machine dictates should be done
* Multi-machine support (client-server, with same API available at both
  ends; clients can be also non-Python)
* ( Minimalist sun state calculator - TBD if this is good idea or if ambient light sensor is desirable )

Code characteristics / goals
============================

* Support for Python 2.7+ / Python 3.4+

* Pure Python solution (so that it runs easily e.g. on OpenWrt without
  python-dev or equivalent)
  
* Correctness - should be robust. Ensured by reasonable unit test coverage
  (and potentially system tests later on)

* As few external dependencies as possible

Requirements
============

* phue (Philips Hue support - pure Python, single .py)
* tox (for unit testing; it will pull py.test and run things inside virtualenv)
* prdb (for database of key-value objects)
* pysyma (for PRDB state synchronization across home)

Design
======

As simple as possible - basically, simple signal mechanism (without
external dependencies as e.g. pysignal is not really maintained), combined
with use of threading where applicable. Integration of third-party
libraries to single-threaded application is too painful so I cannot be
bothered.

Non-goals
=========

* 'efficiency' - all I care is fast development, and relative robustness of
  the final solution.
  
Known bugs
==========

* For some reason, at significant uptime (e.g. ~34 days) around Oct/Nov
  2015 wifi detection started to bug; killed on 20th of Nov.

root      1786  3.4  5.6  20008  7184 pts/0    Sl+  Oct17 1719:34 python /root/python/example/start.py
