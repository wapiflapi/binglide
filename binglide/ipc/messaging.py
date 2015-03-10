# -*- coding: utf-8 -*-

import os
import abc
import json
import logging
import argparse

import zmq
import yaml

from binglide.ipc import dispatching
from binglide.ipc.dispatching import bind


class Endpoint(metaclass=abc.ABCMeta):

    def __init__(self, endpoint, identity=None):
        self.endpoint = endpoint
        self.identity = identity

    @abc.abstractmethod
    def set_endpoint(self, socket):
        pass

    def __call__(self, socket):
        if self.identity is not None:
            socket.identity = identity
        self.set_endpoint(socket)
        return socket

    def __repr__(self):
        return "%s(endpoint=%r, identity=%r)" % (
            self.__class__.__name__, self.endpoint, self.identity)


class BindSocket(Endpoint):

    def set_endpoint(self, socket):
        socket.bind(self.endpoint)


class ConnectSocket(Endpoint):

    def set_endpoint(self, socket):
        socket.connect(self.endpoint)


class Node(dispatching.Dispatcher):

    def __init__(self, zmqctx, socktype, keyidx,
                 logger, assertive=False, loglvl=None):
        super().__init__(assertive)

        self.keyidx = keyidx

        if not isinstance(logger, logging.Logger):
            self.logger = logging.getLogger(logger)
        else:
            self.logger = logger

        if loglvl is not None:
            self.logger.setLevel(loglvl)

        self.zmqctx = zmqctx
        self.socket = self.zmqctx.socket(socktype)
        self.config(self.socket)

    def start(self):
        pass

    def process_events(self, block=False, intercept=None):
        self.logger.debug("processing, block=%s, intercepting=%s" %
                          (block, intercept))

        while block or self.socket.get(zmq.EVENTS) & zmq.POLLIN:

            block = False  # only block once.
            msg = self.socket.recv_multipart()

            self.logger.debug("received: %s" % msg)

            if intercept is not None and intercept(msg):
                return msg[self.keyidx], msg

            self.dispatch(msg[self.keyidx], msg)
            self.logger.debug("dispatch ready.")

        self.logger.debug("stopped processing.")

    def wait_for(self, intercept):
        return self.process_events(block=True, intercept=intercept)

    def wait_for_key(self, key):
        return self.wait_for(lambda m: m[self.keyidx] == key)

    def run(self):

        self.start()

        while True:
            self.logger.debug("MAIN LOOP.")
            self.process_events(block=True)
