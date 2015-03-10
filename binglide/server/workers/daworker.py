# -*- coding: utf-8 -*-

# DAWorkers aren't normal workers. We dont want:
#   - One DAWorker handling several data types (files, streams, ...)
#   - One DAWorker handling several data sourcers (two streams, two files).
#
# DAWorkers should be a class generating a worker service for a given
# DataAccessor Instance. Service name should be generated or specified by
# arguments and be "unique". Instanciating several DAWorkers for the same source
# is probably a stupid thing to do. But I don't think we're in a position to
# check for this.

from binglide.ipc import protocol, utils
from binglide.data import Accessor
from binglide.server.workers import ReportAware, CacheAware

class DAWorker(protocol.Worker, ReportAware, CacheAware):

    def __init__(self, *args, **kwargs):
        self.accessor = self.args.accessor
        self.servicename = "%s://%s" % (self.accessor.__qualname__,
                                        self.accessor.uri)
        super().__init__(self, *args, **kwargs)

    def handle_xrequest(self, meta, body):

        details = self.accessor.get_data(
            body.request.options.offset,
            body.request.options.size,
            body.request.options.sample,
            body.request.options.margin)

        self.commit(*details)
        self.report(*details)


class import_object(object):

    def __init__(self, abc=None):
        self.abc = abc

    def __call__(self, name):
        modulename, objname = name.rsplit('.', 1)
        obj = getattr(import_module(modulename), objname)
        if self.abc is not None and not isinstance(obj, self.abc):
            raise TypeError("Not an instance of %r." % self.abc)
        return obj


class Main(utils.WorkerMain):

    runnable = DAWorker

    def setup(self, parser):
        super().setup(parser)
        parser.add_argument("accessor", type=import_object(abc=Accessor))


if __name__ == '__main__':
    Main()
