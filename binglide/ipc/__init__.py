import zmq

import binglide


def versions():
    return {
        "libzmq": zmq.zmq_version(),
        "pyzmq": zmq.__version__,
        "binglide": binglide.__version__,
        }
