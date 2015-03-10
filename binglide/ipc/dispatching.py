# -*- coding: utf-8 -*-


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
