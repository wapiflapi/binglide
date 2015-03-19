import os
import os.path
import urllib.parse

import numpy

from binglide import config


class CacheManager():

    def __init__(self, cachedir, name=None):

        if name is not None:
            cachedir = os.path.join(cachedir, "%s.cache" % name)

        try:
            os.makedirs(cachedir)
        except FileExistsError:
            pass

        self.cachedir = cachedir

    @classmethod
    def default(cls, namespace="global"):
        cachedir = config.get_default_cache_dir()
        return cls(cachedir, namespace)

    @classmethod
    def for_namespace(cls, namespace, localdir=True):
        cachedir, name = os.path.split(namespace)
        if localdir is True:
            try:
                return cls(cachedir, name)
            except:
                pass  # Fallback to default.
        return cls.default(name)

    def build_cachename(self, key, offset, size):
        return "%s.%s-%s" % (
            key,
            "_".join(str(x) for x in offset),
            "_".join(str(x) for x in size))

    def build_filename(self, cachename):
        cachename = urllib.parse.quote(cachename, safe=":=")
        return os.path.join(self.cachedir, cachename) + ".npz"

    def lookup(self, key, offset, size):
        cachename = self.build_cachename(key, offset, size)
        filename = self.build_filename(cachename)

        try:
            return numpy.load(filename)
        except IOError:
            raise KeyError(cachename)

    def commit(self, key, offset, size, *args, **kwargs):
        cachename = self.build_cachename(key, offset, size)
        filename = self.build_filename(cachename)

        numpy.savez(filename, *args, **kwargs)
