import abc

import numpy


class Accessor(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def uri(self):
        return ""

    @abc.abstractmethod
    def get_data(self, offset, size, sample):
        # This is default value, its short read and indicates an error.
        return bytes(0)


class SamplingMixin(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def sampler(self):
        pass

    @abc.abstractmethod
    def get_data_ns(self, offset, size):
        return bytes(0)

    def get_data(self, offset, size, sample):
        return self.sampler.sample(self.get_data_ns, offset, size, sample)


class SamplingBytesMixin(SamplingMixin, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_bytes_ns(self, offset, size):
        return bytes(0)

    def get_data_ns(self, offset, size):
        data = self.get_bytes_ns(offset[0], size[0])
        return numpy.frombuffer(data, "u1")


class BytesMixin(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_bytes(self, offset, size, sample):
        return bytes(0)

    def get_data(self, offset, size, sample):
        data = self.get_bytes(offset[0], size[0], sample[0])
        return numpy.frombuffer(data, "u1")
