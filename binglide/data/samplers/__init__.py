import abc

import numpy


class Sampler(metaclass=abc.ABCMeta):

    def __init__(self, dtype):
        self.dtype = dtype

    def itersample(offset, size, sample):
        yield (0, size // sample, offset, size, sample)

    @abc.abstractmethod
    def get_sample(getter, offset, size, sample, *args, **kwargs):
        """
        getter -> fct(offset, size, *args, **kwargs)
        """

    def sample(self, getter, offset, size, sample, *args, **kwargs):

        offset = numpy.array(offset)
        size = numpy.array(size)
        sample = numpy.array(sample)

        out = numpy.empty(size // sample, dtype=self.dtype)

        maxread = size  # don't read beyond this
        gotread = numpy.zeros(size.shape)  # this is done

        for do, ds, so, ssz, ss in self.itersample(offset, size, sample):

            ssz = numpy.fmin(ds, out.shape - do)

            # Did we have a short read on all axis before this?
            if (so >= maxread).all():
                continue

            data = self.get_sample(getter, so, ssz, ss, *args, **kwargs)

            # update the point until which we have data
            gotread = numpy.fmax(gotread, so + data.shape)

            # check for any new short reads.
            maxread = numpy.where(data.shape < ssz, so + data.shape, maxread)

            # WTF is there no easier way of doing this. I must be blind.
            out[tuple(map(slice, do, do + data.shape))] = data

        return out[tuple(slice(s) for s in gotread)]
