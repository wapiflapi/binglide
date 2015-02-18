#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc


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

        calbacks = self.dispatchtable.get(key, [])

        for callback in callbacks:
            return callback(*args, **kwargs)

        if self.assertive and not calbacks:
            return self.handle_unknown(key, *args, **kwargs)

    def handle_unknown(self, key, *args, **kwargs):
        raise NotImplementedError("Unknown event key <%s>." % key)
