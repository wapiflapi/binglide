import abc

import numpy

from binglide.data import accessors


class File(accessors.Accessor, metaclass=abc.ABCMeta):

    def __init__(self, path):
        self.path = path

    @property
    def uri(self):
        return "file://%s" % self.path


class MMappedFile(File):

    def __init__(self, path):
        super().__init__(path)
        self.array = numpy.memmap(path, dtype=numpy.uint8, mode='r')

    @accessors.autosample1D(numpy.uint8)
    def get_data(self, offset, size):
        return self.array[offset:offset+size]


class SeekingFile(File):

    def __init__(self, path):
        super().__init__(path)
        self.file = open(path, 'rb')

    @accessors.autosamplebytes
    def get_data(self, offset, size):
        self.file.seek(offset)

        data = b""

        while size:
            newdata = self.file.read(size)
            if not newdata:
                break
            data += newdata
            size -= len(newdata)

        return data
