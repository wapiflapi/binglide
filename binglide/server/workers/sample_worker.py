# -*- coding: utf-8 -*-

import time

from binglide.ipc import protocol, utils


class SampleWorker(protocol.Worker):

    servicename = "sample_worker"

    def handle_xrequest(self, meta, body):

        # Dummy task, lets send several reports.
        for status in range(3):
            time.sleep(2)

            canceled = self.check_canceled(meta)
            if canceled is not None:
                # We could inspect canceled if we wanted to.
                return True

            self.report(meta, {'status': status})

        return True


class Main(utils.Main):
    runnable = SampleWorker


if __name__ == '__main__':
    Main()
