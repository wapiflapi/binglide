#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from binglide.renderers import Renderer

@Renderer.register_painter(None)
def paint_values(colored, data, mixers, coefs):
    for mixer in mixers:
        mixer(colored, data, coefs)
    return colored

@Renderer.register_painter(None)
def paint_ascii(colored, data, mixers, coefs):
    ndata = np.copy(data)

    ndata[data > 0x7e] = 0
    ndata[data < 0x20] = 0
    ndata[data > 0] = 0x255

    for mixer in mixers:
        mixer(colored, ndata, coefs)

    return colored

@Renderer.register_painter(("2D", "3D"))
def paint_asciipos(colored, data, mixers, coefs):
    ndata = np.zeros(data.shape)

    print(data.shape)

    if len(data.shape) == 3:
        l0, h0 = 0x20 * data.shape[0] // 256, 0x7e * data.shape[0] // 256
        l1, h1 = 0x20 * data.shape[1] // 256, 0x7e * data.shape[1] // 256
        l2, h2 = 0x20 * data.shape[2] // 256, 0x7e * data.shape[2] // 256
        ndata[l0:h0, l1:h1, l2:h2] += data[l0:h0, l1:h1, l2:h2] * 0.33
    elif len(data.shape) == 2:
        l0, h0 = 0x20 * data.shape[0] // 256, 0x7e * data.shape[0] // 256
        l1, h1 = 0x20 * data.shape[1] // 256, 0x7e * data.shape[1] // 256
        ndata[l0:h0, l1:h1] += data[l0:h0, l1:h1] * 0.33
    else:
        raise ValueError("asciipos can't handle shape %s" % (data.shape,))

    for mixer in mixers:
        mixer(colored, ndata, coefs)

    return colored


@Renderer.register_painter(("2D", "3D"))
def paint_asciiposx(colored, data, mixers, coefs):
    ndata = np.zeros(data.shape)

    print(data.shape)

    if len(data.shape) == 3:
        l, h = 0x20 * data.shape[0] // 256, 0x7e * data.shape[0] // 256
        ndata[l:h, 0:-1, 0:-1] += data[l:h, 0:-1, 0:-1] * 0.33
        l, h = 0x20 * data.shape[1] // 256, 0x7e * data.shape[1] // 256
        ndata[0:-1, l:h, 0:-1] += data[0:-1, l:h, 0:-1] * 0.33
        l, h = 0x20 * data.shape[2] // 256, 0x7e * data.shape[2] // 256
        ndata[0:-1, 0:-1, l:h] += data[0:-1, 0:-1, l:h] * 0.33
    elif len(data.shape) == 2:
        l, h = 0x20 * data.shape[0] // 256, 0x7e * data.shape[0] // 256
        ndata[l:h, 0:-1] += data[l:h, 0:-1] * 0.33
        l, h = 0x20 * data.shape[1] // 256, 0x7e * data.shape[1] // 256
        ndata[0:-1, l:h] += data[0:-1, l:h] * 0.33
    else:
        raise ValueError("asciipos can't handle shape %s" % (data.shape,))

    for mixer in mixers:
        mixer(colored, ndata, coefs)

    return colored
