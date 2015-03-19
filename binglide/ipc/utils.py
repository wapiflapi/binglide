import os
import argparse

import zmq
import yaml

from binglide import logging
from binglide.ipc.messaging import BindSocket, ConnectSocket  # NOQA


class Main():

    def __init__(self):

        loginfo = yaml.load(os.environ.get('BG_LOGLVL', ''))

        self.loglvl = None

        if isinstance(loginfo, str):
                logging.getLogger('').setLevel(loginfo)
        elif isinstance(loginfo, dict):
            for logger, lvl in loginfo.items():
                logging.getLogger(logger).setLevel(lvl)

        self.zmqctx = zmq.Context()

        self.parser = argparse.ArgumentParser()
        self.setup(self.parser)

        self.args = self.parser.parse_args()
        self.run(self.args)

    def setup(self, parser):
        parser.add_argument("router", type=ConnectSocket)

    def run(self, args):
        runnable = self.runnable(self.zmqctx, args.router,
                                 loglvl=self.loglvl, assertive=True)
        runnable.run()
