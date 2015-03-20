import abc
import math
import functools

import numpy


class Accessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_data(self, offset, size, sample=1, margin=0.0):
        # This is default value, its short read and indicates an error.
        return offset, size, bytes(0)

    @property
    @abc.abstractmethod
    def uri(self):
        return ""


def convertbytes(get_data):

    @functools.wraps(get_data)
    def wrapper(obj, offset, size, *args, **kwargs):

        if len(offset) != 1 or len(size) != 1:
            raise ValueError("offset or size is not unidimensional")

        o, s, d = get_data(obj, offset[0], size[0], *args, **kwargs)
        return [o], [s], numpy.frombuffer(d, "u1")

    return wrapper


class autosample1D():

    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, get_data):

        @functools.wraps(get_data)
        def wrapper(obj, offset, size, sample=1, margin=0.0):

            if len(offset) != 1 or len(size) != 1:
                raise ValueError("offset or size is not unidimensional")

            # Not sure what how this should work if < 0.
            assert sample >= 1

            if sample == 1:
                data = get_data(obj, offset[0], size[0])
                return offset, [len(data)], data

            outsz = size[0] // sample
            out = numpy.empty(outsz, dtype=self.dtype)

            # This looks good. Nothing scientific about it though.
            blksz = math.floor(math.sqrt(size[0] // sample))

            done = 0

            for off in range(0, outsz, blksz):

                maxlen = min(blksz, outsz - off)
                data = get_data(obj, offset[0] + off * sample, maxlen)

                new = len(data)

                out[off:off+new] = data
                done += new

                if new < maxlen:
                    break

            return offset, [done], out[:done]

        return wrapper


def autosamplebytes(get_data):

    @functools.wraps(get_data)
    def wrapper(obj, offset, size):
        data = get_data(obj, offset[0], size[0])
        return numpy.frombuffer(data, "u1")

    return autosample1D(dtype="u1")(wrapper)
