from binglide import logging
from binglide.ipc import protocol
from binglide.server import cache


class InputAwareMixin():

    # TODO: This class should also handle zipping.
    # Probably provide several subclasses according to projections and
    # interpolations. It should be possible to use this alongside the
    # interfaces provided by CacheAwareMixin, from the implementation
    # of CachingConsumer.

    def input_request(self, request, inputidx, *args, **kwargs):
        service = request.inputs[inputidx].service
        return self.request(service, *args, **kwargs)

    def input_request_sync(self, request, inputidx, *args, **kwargs):
        service = request.inputs[inputidx].service
        return self.request_sync(service, *args, **kwargs)


class ReportAwareMixin():

    def report(self, request, meta, body):
        super().report(meta, body)

    def handle_report(self, request, meta, report):

        if not isinstance(report, protocol.Payload):
            raise TypeError("%s must generate Payload reports." %
                            self.__class__.__name__)

        self.report(request, meta, report)

    def handle_canceled(self, reason):
        pass

    # We ignore failures but we need to tell the broker we
    # are ready again after the crash, thus errata=True.
    @logging.logexcept(errata=True)
    def receive_xrequest(self, meta, request):

        for report in self.gen_reports(request):

            canceled = self.check_canceled(meta)
            if canceled is not None:
                self.handle_canceled(canceled)
                break

            if report is None:
                # This is just the worker yielding control
                # to process events. Thanks :-)
                continue

            self.handle_report(request, meta, report)

        return True


class CacheAwareMixin():

    # TODO: This class should also handle chunking.
    # I mean the act of separating a request in chunks.
    # If we need to we can have different types of agregators.

    # This class is aware of the following:
    #  - requests (offset, size, sample, margin)
    #  - attachements.

    def __init__(self, namespace=None, localdir=True):
        if namespace is not None:
            self.cache = cache.CacheManager.for_namespace(namespace, localdir)
        else:
            self.cache = cache.CacheManager.default()

    def generate_key(self, request):
        return "%r:sample=%s" % (self, request.options.sample)

    def commit(self, request, response):

        key = self.generate_key(request)
        offset, size = response.offset, response.size

        self.cache.commit(key, offset, size, *response.attachments)

    # sutff like this

    def list(self, request):
        pass

    def makemesmart(self, request):
        pass


class CachingWorker(CacheAwareMixin, protocol.Worker):

    def __init__(self, *args, namespace=None, localdir=True, **kwargs):
        CacheAwareMixin.__init__(self, namespace, localdir)
        protocol.Worker.__init__(self, *args, **kwargs)


class CachingReporter(ReportAwareMixin, CachingWorker):

    def __init__(self, *args, **kwargs):
        ReportAwareMixin.__init__(self)
        CachingWorker.__init__(self, *args, **kwargs)

    def handle_report(self, request, meta, report):
        super().handle_report(request, meta, report)
        self.commit(request, report)


class CachingConsumer(InputAwareMixin, CachingWorker):

    def __init__(self, *args, **kwargs):
        InputAwareMixin.__init__(self)
        CachingWorker.__init__(self, *args, **kwargs)

    def generate_key(self, request, sufix=""):
        key = ",".join(i.cid for i in request.inputs)
        return "%s:%s" % (key, super().generate_key(request))


class ConsumingReporter(ReportAwareMixin, InputAwareMixin, protocol.Worker):

    def __init__(self, *args, **kwargs):
        InputAwareMixin.__init__(self)
        ReportAwareMixin.__init__(self)
        protocol.Worker.__init__(self, *args, **kwargs)


class CachingConsumingReporter(CachingReporter, CachingConsumer,
                               ConsumingReporter):

    def __init__(self, *args, **kwargs):

        # Avoid diamonds of death.
        #   - (CachingReporter, CachingConsumer) -> CachingWorker -> Worker
        #   - ConsumingReporter -> (..., Worker)

        InputAwareMixin.__init__(self)
        ReportAwareMixin.__init__(self)
        CachingWorker.Worker.__init__(self, *args, **kwargs)
