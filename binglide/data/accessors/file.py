import abc

import numpy

from binglide.data import accessors
from binglide.data.samplers.sparse import SQRTGroups as PreferedSampler


class File(accessors.Accessor, metaclass=abc.ABCMeta):

    def __init__(self, path):
        self.path = path

    @property
    def uri(self):
        return "file://%s" % self.path


class MMappedFile(accessors.SamplingMixin, File):

    sampler = PreferedSampler(numpy.uint8)

    def __init__(self, path):
        super().__init__(path)
        self.array = numpy.memmap(path, dtype=numpy.uint8, mode='r')

    def get_data_ns(self, offset, size):
        return self.array[offset:offset+size]


class SeekingFile(accessors.SamplingBytesMixin, File):

    sampler = PreferedSampler(numpy.uint8)

    def __init__(self, path):
        super().__init__(path)
        self.file = open(path, 'rb')

    def get_bytes_ns(self, offset, size):
        self.file.seek(offset)

        data = b""

        while size:
            newdata = self.file.read(size)
            if not newdata:
                break
            data += newdata
            size -= len(newdata)

        return data
