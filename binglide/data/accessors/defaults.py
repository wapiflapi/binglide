import os

import numpy

from binglide.data import accessors
from binglide.data.samplers.sparse import SQRTGroups as PreferedSampler


class Null(accessors.BytesMixin, accessors.Accessor):

    @property
    def uri(self):
        return "null://"

    def get_bytes(self, offset, size, sample):
        return bytes(0)


class Full(accessors.BytesMixin, accessors.Accessor):

    @property
    def uri(self):
        return "full://"

    def get_bytes(self, offset, size, sample):
        return bytes(size // sample)


class Random(accessors.BytesMixin, accessors.Accessor):

    @property
    def uri(self):
        return "random://"

    def get_bytes(self, offset, size, sample):
        return os.urandom(size // sample)


class Modulus(accessors.BytesMixin, accessors.Accessor):

    @property
    def uri(self):
        return "mod://"

    def get_bytes(self, offset, size, sample):
        return bytearray((offset + b * sample) % 256
                         for b in range(size // sample))


class SampledModulus(accessors.SamplingBytesMixin, accessors.Accessor):

    sampler = PreferedSampler(numpy.uint8)

    @property
    def uri(self):
        return "mod://"

    def get_bytes_ns(self, offset, size):
        return bytearray(range(int(offset), int(offset + size)))


class StaticRandom(accessors.BytesMixin, accessors.Accessor):

    def __init__(self, seed=0):
        self.seed = seed

    @property
    def uri(self):
        return "random://%r" % (self.seed)

    def get_bytes(self, offset, size, sample):

        def hash(x):
            x = x ^ self.seed
            for n in range(7):
                x = ((x >> 8) ^ x) * 0x6B + n
            return x & 0xFF

        return bytearray(hash(i) for i in range(offset, offset+size, sample))
