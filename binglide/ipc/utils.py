# -*- coding: utf-8 -*-

import os
import logging
import argparse

import zmq
import yaml

from binglide.ipc.messaging import BindSocket, ConnectSocket  # NOQA


class Main(object):

    def __init__(self):

        loginfo = yaml.load(os.environ.get('BG_LOGLVL', ''))

        self.loglvl = None

        if isinstance(loginfo, str):

            logging.basicConfig(level=loginfo)
        elif isinstance(loginfo, dict):
            for logger, lvl in loginfo.items():
                logging.getLogger(logger).setLevel(lvl)

        self.zmqctx = zmq.Context()

        self.parser = argparse.ArgumentParser()
        self.setup(self.parser)

        self.args = self.parser.parse_args()
        self.run(self.args)
