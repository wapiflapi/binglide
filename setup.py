#!/usr/bin/env python

import sys
from distutils.core import setup

if sys.version_info < (3, 0):
    sys.stdout.write("Sorry, requires Python 3.x.\n")
    sys.exit(1)

setup(name='binglide',
      version='1.0',
      packages=['binglide'],
      scripts=['bin/binglide'],
      )
