import os

from binglide.data import accessors


class Null(accessors.Accessor):

    @accessors.convertbytes
    def get_data(self, offset, size, sample):
        return bytes(0)

    @property
    def uri(self):
        return "null://"


class Full(accessors.Accessor):

    @accessors.convertbytes
    def get_data(self, offset, size, sample):
        return bytes(size // sample)

    @property
    def uri(self):
        return "full://"


class Random(accessors.Accessor):

    @accessors.convertbytes
    def get_data(self, offset, size, sample):
        return os.urandom(size // sample)

    @property
    def uri(self):
        return "random://"


class StaticRandom(accessors.Accessor):

    def __init__(self, seed=0):
        self.seed = seed

    @accessors.convertbytes
    def get_data(self, offset, size, sample):

        def hash(x):
            x = x ^ self.seed
            for n in range(7):
                x = ((x >> 8) ^ x) * 0x6B + n
            return x & 0xFF

        return bytearray(hash(i) for i in range(offset, offset+size, sample))

    @property
    def uri(self):
        return "random://%r" % (self.seed)
