import logging
import functools
import traceback

from logging import *  # NOQA


def getLogger(logger):
    if isinstance(logger, logging.Logger):
        return logger
    return logging.getLogger(logger)


class logexcept(object):

    def __init__(self, *args, **kwargs):
        self.exceptions = tuple(args) or Exception
        self.logger = kwargs.get('logger')
        self.errata = kwargs.get('errata')
        self.msg = kwargs.get('msg', "{excname}: {excmsg} (in {function!s})")

    def __call__(self, f):

        # FIXME: don't fail if this isn't a method call.

        @functools.wraps(f)
        def wrapper(self_, *args, **kwargs):

            try:
                return f(self_, *args, **kwargs)
            except self.exceptions as e:

                logger = getLogger(self.logger if self.logger is not None
                                   else getattr(self_, 'logger', None))

                logger.critical(self.msg.format(excmsg=e,
                                                excname=e.__class__.__name__,
                                                function=f.__qualname__))
                logger.error(traceback.format_exc())

                return self.errata

        return wrapper
