# -*- coding: utf-8 -*-

from binglide.ipc import utils


class CacheAgregator(utils.Worker):

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.reports = {}

    def handle_report(self, service, reqid, report):
        self.reports[reqid] = (service, report)

    def handle_xrequest(self, meta, request):
        result = None
        tasks = {}
