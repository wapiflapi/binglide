import abc
import functools

import numpy


class Accessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_data(self, offset, size, sample):
        # This is default value, its short read and indicates an error.
        return bytes(0)

    @property
    @abc.abstractmethod
    def uri(self):
        return ""


class autosample():

    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, get_data):
        """
        Implements sampling as a decorator for get_data functions.

        Only decimation is implemented and its not using any legit method. It
        tries to preserve patterns from the original data sources. When
        sampling [0, 1, 2, 3, 4, 5, 6, 7] with factor 2 we obtain [0, 1, 4, 5]
        instead of the naive [0, 2, 4, 6]. The length consecutive bytes to copy
        is computed as sqrt(size // sample) because that works well.
        """

        @functools.wraps(get_data)
        def wrapper(obj, offset, size, sample):

            offset = numpy.array(offset)
            size = numpy.array(size)
            sample = numpy.array(sample)

            if (sample < 1).any():
                # We only handle decimination at the moment.
                raise NotImplementedError("interpolation not implemented")

            if sample.max() == 1:
                return get_data(obj, offset, size)

            outsz = size // sample
            out = numpy.empty(outsz, dtype=self.dtype)

            # This looks good. Nothing scientific about it though.
            fillsz = numpy.floor(numpy.sqrt(size // sample))
            jumpsz = fillsz * sample

            maxread = size  # don't read beyond this
            gotread = numpy.zeros(size.shape)  # this is done

            for blkidx in numpy.ndindex(size // jumpsz):

                dstoff = blkidx * fillsz

                srcoff = offset + blkidx * jumpsz
                srcsz = numpy.fmin(fillsz, out.shape - dstoff)

                # Did we have a short read on all axis before this?
                if (srcoff >= maxread).all():
                    continue

                data = get_data(obj, srcoff, srcsz)

                # update the point until which we have data
                gotread = numpy.fmax(gotread, srcoff + data.shape)

                # check for any new short reads.
                maxread = numpy.where(data.shape < srcsz,
                                      srcoff + data.shape, maxread)

                # WTF is there no easier way of doing this. I must be blind.
                out[tuple(map(slice, dstoff, dstoff + data.shape))] = data

            return out[tuple(slice(s) for s in gotread)]

        return wrapper


def autosamplebytes(get_data):

    @functools.wraps(get_data)
    def wrapper(obj, offset, size):
        data = get_data(obj, offset[0], size[0])
        return numpy.frombuffer(data, "u1")

    return autosample(dtype="u1")(wrapper)


def convertbytes(get_data):

    @functools.wraps(get_data)
    def wrapper(obj, offset, size, sample):
        data = get_data(obj, offset[0], size[0], sample[0])
        return numpy.frombuffer(data, "u1")

    return wrapper
