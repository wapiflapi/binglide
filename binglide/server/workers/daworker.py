import importlib

from binglide.ipc import bodyfmt, utils
from binglide.data import Accessor
from binglide.server.workers import CachedReporter


class DAWorker(CachedReporter):

    def __init__(self, accessor, *args, **kwargs):
        self.accessor = accessor
        self.servicename = self.accessor.uri
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return 'daworker(%r)' % self.servicename

    def gen_reports(self, body):

        *meta, data = self.accessor.get_data(
            body.options.offset, body.options.size,
            body.options.sample, body.options.margin)

        response = bodyfmt.BodyFmt()
        (response.offset, response.size,
         response.sample, response.margin) = meta

        yield response, data


class import_object(object):

    def __init__(self, abc=None):
        self.abc = abc

    def __call__(self, name):
        modulename, objname = name.rsplit('.', 1)
        obj = getattr(importlib.import_module(modulename), objname)
        if self.abc is not None and not issubclass(obj, self.abc):
            raise TypeError("Not an instance of %r." % self.abc)
        return obj


class Main(utils.Main):

    def setup(self, parser):
        super().setup(parser)
        parser.add_argument("accessor", type=import_object(abc=Accessor))

    def run(self, args):

        accessor = args.accessor()

        runnable = DAWorker(accessor, self.zmqctx, args.router,
                            loglvl=self.loglvl, assertive=True)
        runnable.run()


if __name__ == '__main__':
    Main()
