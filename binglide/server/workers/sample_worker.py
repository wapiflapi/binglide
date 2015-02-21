#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from binglide.ipc import utils


class SampleWorker(utils.Worker):

    servicename = "sample_worker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canceled = set()

    def handle_xrequest(self, meta, body):

        # Dummy task, lets send several reports.
        for status in range(3):
            time.sleep(2)

            canceled = self.check_canceled(meta)
            if canceled is not None:
                # We could inspect canceled if we wanted to.
                return

            self.report(meta, {'status': status})

        self.ready()


class Main(utils.Main):

    def setup(self, parser):
        parser.add_argument("router", type=utils.ConnectSocket)

    def run(self, args):
        worker = SampleWorker(self.zmqctx, args.router,
                              loglvl=self.loglvl, assertive=True)
        worker.run()


if __name__ == '__main__':
    Main()
