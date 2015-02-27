#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import abc
import json
import logging
import argparse

import zmq
import yaml

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


class Dispatcher(object):

    bind = bind

    def __init__(self, assertive=False):
        self.assertive = assertive

        # Not sure if we want this or not.
        if not issubclass(self.bind, bind):
            raise TypeError("bind should be subclass of %r" % bind)

        if not hasattr(self, 'dispatchtable'):
            self.dispatchtable = {}

        for attr in dir(self):
            handler = getattr(self, attr)
            if not callable(handler) or not hasattr(handler, '_handles'):
                continue
            for key in handler._handles:
                self.dispatchtable.setdefault(key, []).append(handler)

    def dispatch(self, key, *args, **kwargs):

        callbacks = self.dispatchtable.get(key, [])

        for callback in callbacks:
            return callback(*args, **kwargs)

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

    def process_events(self, block=False, intercept=None):
        self.logger.debug("processing, block=%s, intercept=%s" % (block, intercept))

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


class Peer(Node):

    def __init__(self, zmqctx, keyidx, logger, *args, **kwargs):
        super().__init__(zmqctx, zmq.DEALER, keyidx, logger,
                         *args, **kwargs)

    def encode_payload(self, payload):
        return bytes(json.dumps(payload), 'utf8')

    def decode_payload(self, payload):
        return json.loads(str(payload, 'utf8'))


class Client(Peer):

    def __init__(self, zmqctx, config, logger, *args, **kwargs):
        self.config = config
        super().__init__(zmqctx, 0, logger, *args, **kwargs)
        self.reqid = 0

    def wait_for_reqid(self, reqid):
        return self.wait_for(lambda m: m[2] == reqid)

    def request(self, service, body):

        self.reqid = self.reqid + 1

        service = bytes(service, 'utf8')
        reqid = bytes("%d" % self.reqid, 'utf8')
        body = self.encode_payload(body)

        msg = [protocol.REQUEST, service, reqid, b'', body]
        self.socket.send_multipart(msg)

        return reqid

    def request_sync(self, service, body):
        # This needs a timeout because there is no garantee the network will
        # answer. Also there might be more than one answer, in that case the
        # user can continue to monitor reqid.

        thisreqid = self.request(service, body)
        key, msg = self.wait_for_reqid(thisreqid)
        service, reqid, body = self.parse_report(msg)
        return reqid, body

    def cancel(self, reqid, body=None):
        body = self.encode_payload({} if body is None else body)
        msg = [protocol.CANCEL, b'', reqid, b'', body]
        self.socket.send_multipart(msg)

    def list(self):
        self.socket.send_multipart([protocol.LIST])

    def list_sync(self):
        self.list()
        key, msg = self.wait_for_key(protocol.LIST)
        return [str(service, 'utf8') for service in msg[1:]]

    def parse_report(self, msg):
        # service, reqid, body
        return str(msg[1], 'utf8'), msg[2], self.decode_payload(msg[4])

    @bind(protocol.REPORT)
    def on_report(self, msg):
        service, reqid, body = self.parse_report(msg)
        self.handle_report(service, reqid, body)


class Worker(Client):

    def __init__(self, zmqctx, config, *args, **kwargs):
        super().__init__(zmqctx, config, self.get_logger(), *args, **kwargs)
        self.canceledjobs = {}

    def get_logger(self):
        return 'binglide.server.workers.%s' % self.servicename

    def get_service(self):
        return bytes(self.servicename, 'utf8')

    def start(self):
        self.ready()

    def ready(self):
        msg = [protocol.READY, self.get_service()]
        self.socket.send_multipart(msg)

    def get_ukey(self, meta):
        retaddr, reqid, clientid = meta
        return (reqid, clientid)

    def report(self, meta, body):
        retaddr, reqid, clientid = meta
        body = self.encode_payload(body)
        self.socket.send_multipart([protocol.XREPORT, retaddr,
                                    reqid, clientid, body])

    def check_canceled(self, meta):

        self.process_events()

        ukey = self.get_ukey(meta)
        return self.canceledjobs.pop(ukey, None)

    def handle_xcancel(self, meta, body):
        self.canceledjobs[self.get_ukey(meta)] = body

    @bind(protocol.XREQUEST)
    def on_xrequest(self, msg):
        _, retaddr, reqid, clientid, body = msg
        body = self.decode_payload(body)
        if self.handle_xrequest((retaddr, reqid, clientid), body):
            self.ready()

    @bind(protocol.XCANCEL)
    def on_xcancel(self, msg):
        _, retaddr, reqid, clientid, body = msg
        body = self.decode_payload(body)
        if self.handle_xcancel((retaddr, reqid, clientid), body):
            self.ready()

    @bind(protocol.DISCONNECT)
    def on_disconnect(self, msg):
        sys.exit(0)


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
