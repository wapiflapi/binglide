# -*- coding: utf-8 -*-

from binglide.data.accessors import Accessor


class Full(Accessor):

    def get_data(self, offset, size, sample=1.0, margin=0.0):
        return offset, size, sample, margin, bytes(size)


class Null(Accessor):

    def get_data(self, offset, size, sample=1.0, margin=0.0):
        return offset, 0, sample, margin, bytes(0)
