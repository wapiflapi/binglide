#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import zmq

from binglide.ipc import utils, protocol


class SampleWorker(utils.Worker):

    servicename = "sample_worker"

    def __init__(self, *args, **kwargs):
        super().__init__(zmq.DEALER, *args, **kwargs)

    def start(self):
        self.send_ready()

    def send_ready(self):
        msg = [protocol.READY, self.get_service()]
        self.socket.send_multipart(msg)

    @utils.bind(protocol.XREQUEST)
    def on_xrequest(self, msg):
        self.logger.info("on_xrequest")

    @utils.bind(protocol.XCANCEL)
    def on_xcancel(self, msg):
        self.logger.info("on_xcancel")

    @utils.bind(protocol.DISCONNECT)
    def on_disconnect(self, msg):
        sys.exit(0)


class Main(utils.Main):

    def setup(self, parser):
        parser.add_argument("router", type=utils.Connect)

    def run(self, args):
        worker = SampleWorker(self.zmqctx, args.router)
        worker.run()


if __name__ == '__main__':
    Main()
