import logging
import functools
import traceback

from logging import *  # NOQA


# Cammel case because proxy for logging.
def getLogger(logger):
    if isinstance(logger, logging.Logger):
        return logger
    return logging.getLogger(logger)


def log_exception(e, logger=None, msg="{excname}: {excmsg}", **kwargs):
    logger = getLogger(logger)

    logger.critical(msg.format(excname=e.__class__.__name__,
                               excmsg=e, **kwargs))
    logger.error(traceback.format_exc())


class logexcept():

    def __init__(self, *args, logger=None, errata=None,
                 msg="{excname}: {excmsg} (in {function!s})",
                 whitelist=(KeyboardInterrupt,)):
        self.exceptions = tuple(args) or Exception
        self.whitelist = whitelist
        self.logger = logger
        self.errata = errata
        self.msg = msg

    def __call__(self, f):

        # FIXME: don't fail if this isn't a method call.

        @functools.wraps(f)
        def wrapper(self_, *args, **kwargs):

            try:
                return f(self_, *args, **kwargs)
            except self.whitelist as e:
                raise
            except self.exceptions as e:

                if self.logger is None:
                    logger = getattr(self_, 'logger', None)
                else:
                    logger = self.logger

                log_exception(e, logger=logger,
                              msg=self.msg, function=f.__name__)

                return self.errata

        return wrapper
