import os

from binglide.data import Accessor


class Null(Accessor):

    def get_data(self, offset, size, sample=1, margin=0.0):
        return offset, 0, bytes(0)

    @property
    def uri(self):
        return "null://"


class Full(Accessor):

    def get_data(self, offset, size, sample=1, margin=0.0):
        return offset, size, bytes(size // sample)

    @property
    def uri(self):
        return "full://"


class Random(Accessor):

    def get_data(self, offset, size, sample=1, margin=0.0):
        return offset, size, os.urandom(size // sample)

    @property
    def uri(self):
        return "random://"
