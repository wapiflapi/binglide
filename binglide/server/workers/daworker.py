import argparse
import importlib

import yaml
import numpy

from binglide.ipc import protocol, utils
from binglide.data import Accessor
from binglide.server.workers import CachingReporter


class DAWorker(CachingReporter):

    def __init__(self, accessor, *args, **kwargs):
        self.accessor = accessor
        self.servicename = self.accessor.uri
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return 'daworker(%r)' % self.servicename

    def gen_reports(self, body):

        offset, size, data = self.accessor.get_data(
            body.options.offset[0], body.options.size[0],
            body.options.sample, body.options.margin)

        response = protocol.Payload()
        response.offset = (offset,)
        response.size = (size,)

        response.attachments = [numpy.frombuffer(data, "u1")]

        yield response


class import_object():

    def __init__(self, abc=None):
        self.abc = abc

    def __call__(self, name):
        modname, objname = name.rsplit('.', 1)
        try:
            obj = getattr(importlib.import_module(modname), objname)
        except:
            raise ValueError("Can't import %r from %r." % (objname, modname))
        if self.abc is not None and not issubclass(obj, self.abc):
            raise TypeError("Not an instance of %r." % self.abc)
        return obj


class Main(utils.Main):

    def parse_accessor(self, opt):
        try:
            return import_object(abc=Accessor)(opt)
        except Exception as e:
            raise argparse.ArgumentTypeError(str(e))

    def parse_opt(self, opt):
        try:
            return yaml.load(opt)
        except:
            raise argparse.ArgumentTypeError("Must be valid YAML")

    def parse_kwopt(self, kwopt):
        try:
            kw, opt = kwopt.split('=', 1)
        except:
            raise argparse.ArgumentTypeError("Must be 'name=value'")
        return kw, self.parse_opt(opt)

    def setup(self, parser):
        super().setup(parser)
        parser.add_argument("accessor", type=self.parse_accessor)
        parser.add_argument("-O", "--kwopt", action='append',
                            type=self.parse_kwopt, default=[])
        parser.add_argument("-o", "--opt", action='append',
                            type=self.parse_opt, default=[])

    def runnable(self, args):
        accessor = args.accessor(*args.opt, **dict(args.kwopt))
        return DAWorker(accessor, self.zmqctx, args.router,
                        loglvl=self.loglvl, assertive=True)


if __name__ == '__main__':
    Main()
