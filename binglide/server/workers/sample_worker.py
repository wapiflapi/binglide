#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binglide.ipc import utils, protocol


class SampleWorker(utils.Worker):

    servicename = "sample_worker"

    @utils.bind(protocol.XREQUEST)
    def on_xrequest(self, msg):
        self.logger.info("on_xrequest")

    @utils.bind(protocol.XCANCEL)
    def on_xcancel(self, msg):
        self.logger.info("on_xcancel")


class Main(utils.Main):

    def setup(self, parser):
        parser.add_argument("router", type=utils.ConnectSocket)

    def run(self, args):
        worker = SampleWorker(self.zmqctx, args.router, loglvl=self.loglvl)
        worker.run()


if __name__ == '__main__':
    Main()
