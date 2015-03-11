import os

from binglide.data import Accessor


class Null(Accessor):

    def get_data(self, offset, size, sample=1.0, margin=0.0):
        return offset, 0, sample, margin, bytes(0)

    @property
    def uri(self):
        return "null://"


class Full(Accessor):

    def get_data(self, offset, size, sample=1.0, margin=0.0):
        return offset, size, sample, margin, bytes(int(sample * size))

    @property
    def uri(self):
        return "full://"


class Random(Accessor):

    def get_data(self, offset, size, sample=1.0, margin=0.0):
        return offset, size, sample, margin, os.urandom(int(sample * size))

    @property
    def uri(self):
        return "random://"
