#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import abc
import logging
import argparse

import zmq

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


class Bind(Endpoint):

    def set_endpoint(self, socket):
        socket.bind(self.endpoint)


class Connect(Endpoint):

    def set_endpoint(self, socket):
        socket.connect(self.endpoint)


class bind(object):

    def __init__(self, *args):
        self.keys = args

    def __call__(self, f):
        f._handles = self.keys
        return f


class DispatcherMeta(type):

    def __new__(cls, name, bases, attrs):

        # Not sure if we want this or not.
        if not issubclass(attrs.setdefault('bind', bind), bind):
            raise TypeError("bind should be subclass of %r" % bind)

        dispatchtable = attrs.setdefault('dispatchtable', {})
        for value in attrs.values():
            for key in getattr(value, '_handles', []):
                dispatchtable.setdefault(key, []).append(value)

        return super().__new__(cls, name, bases, attrs)


class Dispatcher(metaclass=DispatcherMeta):

    def __init__(self, assertive=False):
        self.assertive = assertive

    def dispatch(self, key, *args, **kwargs):

        callbacks = self.dispatchtable.get(key, [])

        for callback in callbacks:
            return callback(self, *args, **kwargs)

        if self.assertive and not calbacks:
            return self.handle_unknown(key, *args, **kwargs)

    def handle_unknown(self, key, *args, **kwargs):
        raise NotImplementedError("Unknown event key <%s>." % key)


class Worker(Dispatcher):

    servicename = None

    def __init__(self, socktype, zmqctx, config, assertive=False, loglvl=None):
        super().__init__()

        self.logger = logging.getLogger(
            'binglide.server.workers.%s' % self.servicename)

        if loglvl is None:
            loglvl = os.environ.get('BG_LOGLVL', None)
        if loglvl is not None:
            self.logger.setLevel(loglvl)

        self.zmqctx = zmqctx
        self.socket = self.zmqctx.socket(socktype)
        config(self.socket)

    def get_service(self):
        return bytes(self.servicename, 'utf8')

    def start(self):
        pass

    def run(self):

        self.start()

        while True:
            msg = self.socket.recv_multipart()
            self.logger.info(msg)
            self.dispatch(msg[1], msg)


class Main(object):

    def __init__(self):
        self.zmqctx = zmq.Context()

        self.parser = argparse.ArgumentParser()
        self.setup(self.parser)

        self.args = self.parser.parse_args()
        self.run(self.args)
