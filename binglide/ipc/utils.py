#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import abc
import logging
import argparse

import zmq

from binglide.ipc import protocol


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


class bind(object):

    def __init__(self, *args):
        self.keys = args

    def __call__(self, f):
        if self.keys:
            f._handles = self.keys
        elif f.__name__.startswith('on_'):
            f._handles = [f.__name__[3:]]
        else:
            raise RuntimeError("No obvious binding for %s." % f)

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

        if self.assertive and not callbacks:
            return self.handle_unknown(key, *args, **kwargs)

    def handle_unknown(self, key, *args, **kwargs):
        raise NotImplementedError("Unknown event key <%s>." % key)


class Node(Dispatcher):

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

    def process_events(self, block=False, intercept=[]):

        while block or self.socket.get(zmq.EVENTS) & zmq.POLLIN:
            block = False # only block once.
            msg = self.socket.recv_multipart()

            self.logger.debug("received: %s" % msg)

            if msg[self.keyidx] in intercept:
                return msg[self.keyidx], msg

            self.dispatch(msg[self.keyidx], msg)

    def wait_for(self, keys):
        return self.process_events(block=True, intercept=keys)

    def run(self):

        self.start()

        while True:
            self.process_events(block=True)


class Peer(Node):

    def __init__(self, zmqctx, keyidx, logger, *args, **kwargs):
        super().__init__(zmqctx, zmq.DEALER, keyidx, logger,
                         *args, **kwargs)


class Worker(Peer):

    def __init__(self, zmqctx, config, *args, **kwargs):
        self.config = config
        super().__init__(zmqctx, 0,
                         'binglide.server.workers.%s' % self.servicename,
                         *args, **kwargs)

    def get_service(self):
        return bytes(self.servicename, 'utf8')

    def start(self):
        self.send_ready()

    def send_ready(self):
        msg = [protocol.READY, self.get_service()]
        self.socket.send_multipart(msg)

    @bind(protocol.DISCONNECT)
    def on_disconnect(self, msg):
        sys.exit(0)


class Client(Peer):

    def __init__(self, zmqctx, config, logger, *args, **kwargs):
        self.config = config
        super().__init__(zmqctx, 0, logger, *args, **kwargs)
        self.reqid = 0

    def request(self, service, body):

        self.reqid = self.reqid + 1
        reqid = bytes("%d" % self.reqid, 'utf8')

        msg = [protocol.REQUEST, service, reqid, b'', body]
        self.socket.send_multipart(msg)

        return reqid

    def request_sync(self, service, body):
        # This needs a timeout because there is no garantee the network will
        # answer. Also there might be more than answer, in that case the user
        # can continue to monitor reqid.

        thisreqid = self.request(service, body)

        while True:
            key, msg = self.wait_for((protocol.REPORT,))
            service, reqid, body = self.parse_report(msg)
            if reqid == thisreqid:
                return reqid, body

    def list(self):
        self.socket.send_multipart([protocol.LIST])

    def list_sync(self):
        self.list()
        key, msg = self.wait_for((protocol.LIST,))
        return [str(service, 'utf8') for service in msg[1:]]

    def parse_report(self, msg):
        # service, reqid, body
        return msg[1], msg[2], msg[5]

    @bind(protocol.REPORT)
    def on_report(self, msg):
        service, reqid, body = self.parse_report(msg)
        self.handle_report(self, service, reqid, body)


class Main(object):

    def __init__(self):

        self.loglvl = os.environ.get('BG_LOGLVL', None)
        if self.loglvl is not None:
            logging.basicConfig(level=self.loglvl)

        self.zmqctx = zmq.Context()

        self.parser = argparse.ArgumentParser()
        self.setup(self.parser)

        self.args = self.parser.parse_args()
        self.run(self.args)
