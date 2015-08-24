#
# $Id: Makefile $
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2015 Markus Stenberg
#
# Created:       Mon Aug 24 10:33:31 2015 mstenber
# Last modified: Mon Aug 24 10:58:40 2015 mstenber
# Edit time:     4 min
#
#

# This is convenience stuff just for my home infra - yours is probably
# different, so steer clear :)

PYTHON=python3.4
RSYNCTARGETS=../example ../kodinhenki ../../prdb/prdb ../../pysyma/pysyma

all: local cer.push pi.push

local:
	(cd ../../prdb && tox && $(PYTHON) setup.py install)
	(cd ../../pysyma && tox && $(PYTHON) setup.py install)
	(cd .. && tox && $(PYTHON) setup.py install)

cer.push:
	rsync -a --delete $(RSYNCTARGETS) cer.lan:python

pi.push:
	rsync -a --delete $(RSYNCTARGETS) raspberrypi.lan:python
