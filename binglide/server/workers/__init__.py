# -*- coding: utf-8 -*-

"""
Regroup all of the default workers that ship with binglide.
"""

class ReportAware(object):

    def report(self, *details):
        pass


class CacheAware(object):

    def commit(self, *details):
        pass
