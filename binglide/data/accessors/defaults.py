import os

from binglide.data import accessors


class Null(accessors.Accessor):

    @accessors.convertbytes
    def get_data(self, offset, size, sample=1, margin=0.0):
        return offset, 0, bytes(0)

    @property
    def uri(self):
        return "null://"


class Full(accessors.Accessor):

    @accessors.convertbytes
    def get_data(self, offset, size, sample=1, margin=0.0):
        return offset, size, bytes(size // sample)

    @property
    def uri(self):
        return "full://"


class Random(accessors.Accessor):

    @accessors.convertbytes
    def get_data(self, offset, size, sample=1, margin=0.0):
        print("Random", self, offset, size, sample, size // sample)
        return offset, size, os.urandom(size // sample)

    @property
    def uri(self):
        return "random://"


class StaticRandom(accessors.Accessor):

    def __init__(self, seed=0):
        self.seed = seed

    @accessors.convertbytes
    def get_data(self, offset, size, sample=1, margin=0.0):

        def hash(x):
            x = x ^ self.seed
            for n in range(7):
                x = ((x >> 8) ^ x) * 0x6B + n
            return x & 0xFF

        data = bytearray(hash(i) for i in range(offset, offset+size, sample))
        return offset, size, data

    @property
    def uri(self):
        return "random://%r" % (self.seed)
