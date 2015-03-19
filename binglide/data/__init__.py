import abc


class Accessor(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_data(self, offset, size, sample=1, margin=0.0):
        # This is default value, its short read and indicates an error.
        return offset, size, bytes(0)

    @property
    @abc.abstractmethod
    def uri(self):
        return ""
