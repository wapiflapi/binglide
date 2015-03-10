# -*- coding: utf-8 -*-

import abc

class Accessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_data(self, offset, size, sample=1.0, margin=0.0):
        # This is default value, its short read and indicates an error.
        return offset, 0, sample, margin, bytes(0)

    @property
    @abc.abstractmethod
    def uri(self):
        return ""
