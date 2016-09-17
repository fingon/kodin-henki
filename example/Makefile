#
# $Id: Makefile $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2015 Markus Stenberg
#
# Created:       Mon Aug 24 10:33:31 2015 mstenber
# Last modified: Sat Sep 17 09:54:17 2016 mstenber
# Edit time:     6 min
#
#

# This is convenience stuff just for my home infra - yours is probably
# different, so steer clear :)

PYTHON=python3
RSYNCTARGETS=../example ../kodinhenki ../../prdb/prdb ../../pysyma/pysyma

all: local push

local:
	(cd ../../prdb && tox && $(PYTHON) setup.py install)
	(cd ../../pysyma && tox && $(PYTHON) setup.py install)
	(cd .. && tox && $(PYTHON) setup.py install)

push: cer.push pi.push

cer.push:
	rsync -a --delete $(RSYNCTARGETS) cer.lan:python

pi.push:
	rsync -a --delete $(RSYNCTARGETS) raspberrypi.lan:python
