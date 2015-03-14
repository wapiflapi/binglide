from binglide import logging
from binglide.ipc import protocol


class InputAware(object):

    def get_chunk(self, request, inputidx, *args):
        raise NotImplementedError()


class ReportAware(object):

    def report(self, request, meta, body):
        super().report(meta, body)


class CacheAware(object):

    def commit(self, request, body):
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

            if not isinstance(report, protocol.Payload):
                raise TypeError("%s must generate Payload reports." %
                                self.__class__.__name__)

            self.commit(body, report)
            self.report(body, meta, report)

        return True

    def handle_canceled(self, reason):
        pass


class AllAware(InputAware, CachedReporter):
    pass
