from binglide import logging
from binglide.ipc import protocol, bodyfmt


class InputAware(object):

    def get_chunk(self, request, inputidx, *args):
        raise NotImplementedError()


class ReportAware(object):

    def report(self, request, meta, body, data=None):
        super().report(meta, body, data)


class CacheAware(object):

    def commit(self, request, body, data=None):
        pass


class CachedReporter(CacheAware, ReportAware, protocol.Worker):

    # We ignore failures but we need to tell the broker we
    # are ready again after the crash, thus errata=True.
    @logging.logexcept(errata=True)
    def handle_xrequest(self, meta, body):

        for report in self.gen_reports(body):

            canceled = self.check_canceled(meta)
            if canceled is not None:
                self.handle_canceled(canceled)
                break

            if report is None:
                # This is just the worker yielding control
                # to process events. Thanks :-)
                continue

            try:
                report, data = report
            except:
                data = None

            if not isinstance(report, bodyfmt.BodyFmt):
                raise TypeError("%s must generate BodyFmt reports.",
                                self.name)

            self.commit(body, report, data)
            self.report(body, meta, report, data)

        return True

    def handle_canceled(self, reason):
        pass


class AllAware(InputAware, CachedReporter):
    pass
