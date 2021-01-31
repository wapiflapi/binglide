#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import operator
from functools import reduce
from math import floor, ceil

import numpy as np

from binglide.renderers import Renderer

@Renderer.register_projector((("1D", "2D", "3D"), ("1D", "2D", "3D")))
def proj_scanline(dst, data, shape):

    # We get colored data. Carefull for the extra dimension.
    # Shape doesnt have RGBA dimension.

    size = data.size / 4 # Ignore RGBA values.

    ratio = size / reduce(operator.mul, shape)
    ratio = pow(ratio, 1/len(shape))

    rshape_c = [int(ceil(ratio * x)) for x in shape]
    rshape = [int(ratio * x) for x in shape]

    for i, c in enumerate(rshape_c):
        rshape[i] = c
        nsize = reduce(operator.mul, rshape)
        if nsize >= size:
            break

    assert nsize >= size

    # Now we but RGBA dimmension back in the final shape.
    rshape.append(4)

    data = data.reshape((size, 4))
    data = np.pad(data, ((0, np.int32(nsize - size)), (0, 0)), 'constant')
    data = data.reshape(rshape, order='F')

    return data

def proj_scanline_lookup(data_shape, proj_shape, proj_pt):

    data_shape = data_shape[:-1]
    proj_shape = proj_shape[:-1]


    # print("scanline lookup: %s/%s ..." % (proj_pt, proj_shape))

    pt, acc = 0, 1
    for d, p in zip(proj_shape, proj_pt):
        # print("\tpt += %d * %d")
        pt += acc * p
        acc = acc * d

    p = pt
    data_pt = ()
    for d in reversed(data_shape[1:]):
        # print("p, r = divmod(%s, %s)" % (p, d))
        p, r = divmod(p, d)
        data_pt += (r,)
    data_pt += (p,)

    # print("scanline lookup: %s/%s =  %s -> %s" % (proj_pt, proj_shape, pt, data_pt))

    return data_pt

proj_scanline.lookup = proj_scanline_lookup

@Renderer.register_projector(lambda src, dst: src == dst)
def proj_identity(dst, data, shape):
    return data


def proj_identity_lookup(data_shape, proj_shape, proj_pt):
    return proj_pt

proj_identity.lookup = proj_identity_lookup
