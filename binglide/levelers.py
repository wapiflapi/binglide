#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import reduce
from operator import itemgetter, mul

import numpy as np

from binglide.renderers import Renderer

@Renderer.register_leveler(None)
def lvl_256proj(dst, data, shape):

    l = np.amin(data)
    h = np.amax(data)

    print("leveling: %s %s" % (l, h))

    return (data - l) * ((l + h) / 255)

@Renderer.register_leveler(None)
def lvl_clip(dst, data, shape):

    l = np.amin(data)
    h = np.amax(data)

    print("cliping: %s %s" % (l, h))

    h = np.amax(data)
    return data

@Renderer.register_leveler(('2DS', '3DS'))
def lvl_cumul256proj_NDS(dst, data, shape):

    print("leveling %s" % (shape,))

    print("\tsorting. %d / %d = %d%%" % (
            len(data), reduce(mul, shape),
            len(data) * 100 / reduce(mul, shape)))
    tgrams = sorted(data.items(), key=itemgetter(1))
    print("\tdone sorting.")

    hist = np.zeros(shape)

    nbtg = float(sum(t[1] for t in tgrams))

    thresold = nbtg / len(tgrams) * 0.5

    acc = 0
    for t, v in tgrams:
        acc += v
        if v > thresold:
            hist[t] = acc

    print("\tleveling.")

    hist = hist * 255 / nbtg

    print("\tdone.")
    return hist
