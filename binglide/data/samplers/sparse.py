import numpy

from binglide.data.samplers import Sampler


class SQRTGroups(Sampler):

    def itersample(self, offset, size, sample):
        """
        Only decimation is implemented and its not using any legit method. It
        tries to preserve patterns from the original data sources. When
        sampling [0, 1, 2, 3, 4, 5, 6, 7] with factor 2 we obtain [0, 1, 4, 5]
        instead of the naive [0, 2, 4, 6]. The length consecutive bytes to copy
        is computed as sqrt(size // sample) because that works well.
        """

        fillsz = numpy.floor(numpy.sqrt(size // sample))
        jumpsz = fillsz * sample

        for blkidx in numpy.ndindex(size // jumpsz):
            dstoff = blkidx * fillsz
            srcoff = offset + blkidx * jumpsz
            yield dstoff, fillsz, srcoff, fillsz, 1

    def get_sample(self, getter, offset, size, sample, *args, **kwargs):
        # We always have sample == 1 so we can delegate to get_data.
        return getter(offset, size, *args, **kwargs)
