#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from math import log

import numpy as np

try:
    from numba import jit
except ImportError:
    print("numba is not available! Entropy calculation will be *slow*.")
    jit = lambda *a, **k: lambda f: f

from binglide.utils import *

class identity(object):

    def __init__(self):
        self.data = None
        self.low = None
        self.high = None

        self.cached = None

    def set_data(self, data):
        self.data = data
        self.cached = None

        print("Set data for %s" % self)

        if self.low is None or any(r < 0 for r, d in zip(self.low, data.shape)):
            self.low = tuple(0 for _ in data.shape)

        if self.high is None or any(r > d for r, d in zip(self.high, data.shape)):
            self.high = data.shape

    def get_ddim(self):
        return ddim_from_shape(self.data.shape)

    def get_shape(self):
        return self.data.shape

    def lookup(self, pt):
        return tuple(l + p for l, p in zip(self.low, pt))

    def set_region(self, low, high):
        self.low = low
        self.high = high
        self.cached = None

    def get_data(self):
        if self.data is None:
            return

        if self.cached is None:
            # print("%s calc data low=%s, high=%s" % (self.__class__.__name__, self.low, self.high))
            self.cached = self.calc_data()
            # print("\tGot %s: %s out of %s" % (self.get_ddim(), self.cached.shape, self.data.shape))
        return self.cached

    def calc_data(self):
        indx = [slice(l, h) for l, h in zip(self.low, self.high)]
        return self.data[indx]



def compute_hist(data, start, end, n, s):
    hist = {}

    end = max(start, end - n + 1)
    for i in xrange(start, end):
        if n == 3:
            t = (data[i], data[i+1], data[i+2])
        else:
            t = (data[i], data[i+1])
        # assert t < s**n, data[i:i+3]
        # The above is way faster than:
        # t = tuple(self.data[i:i+n])
        hist[t] = hist.get(t, 0) + 1

    return hist

class ngrams(identity):

    s = 128

    def set_data(self, data):
        assert len(data.shape) == 1
        super().set_data(data)
        # No idea why I need this cast.
        self.rdata = (data // (256 / self.s)).astype("uint8")
        self.compute_blocks()

    def get_ddim(self):
        return '%dDS' % self.n

    def get_shape(self):
        return (self.s,) * self.n

    def compute_blocks(self):

        self.blocks = []

        # We need to be carefull with blocksizes.
        # S = nb_blocks * avg_nb_ngrams_per_block
        # We want to maximize the number of blocks while keeping
        # the total size under a limit.
        # Basicaly this is a reverse birthday paradox problem.
        # I don't feel like minimizing this function so I'll just compute it.

        limit = 10 * 2**20
        optim = 1024*256

        nb_pos = self.s ** self.n

        maxbs = None
        blocksize = 1
        while blocksize <= 2**self.rdata.shape[0].bit_length():

            nb_blocks = self.rdata.shape[0] / blocksize
            v = nb_pos * (1 - ((nb_pos-1) / nb_pos) ** blocksize)
            s = nb_blocks * v

            # print("%.2f blocks: %.2f*%d(%d) = %d." % (
            #         nb_blocks, nb_blocks, blocksize, v, nb_blocks * v))

            if s <= limit and (maxbs is None or abs(optim - blocksize) < abs(optim - maxbs)):
                maxbs = blocksize

            blocksize *= 2

        if maxbs is None:
            maxbs = 2**self.rdata.shape[0].bit_length()

        self.blocksize = maxbs

        nb_blocks = self.rdata.shape[0] / self.blocksize


        v = nb_pos * (1 - ((nb_pos-1) / nb_pos) ** self.blocksize)
        print("%.2f blocks: %.2f*%d(%d) = %d." % (
                nb_blocks, nb_blocks, self.blocksize, v, nb_blocks * v),
              end=" ")

        for i, start in enumerate(range(0, self.rdata.shape[0], self.blocksize)):
            end = min(self.rdata.shape[0], start + self.blocksize)
            print("%d, " % i, end="")
            sys.stdout.flush()
            self.blocks.append(compute_hist(self.rdata, start, end, self.n, self.s))
        print()

    def calc_data(self):

        # return self.blocks[0]

        l = int(max(self.low[0], 0))
        h = int(min(self.high[0], self.rdata.shape[0]))

        lb = min(h, (l + self.blocksize - 1) & ~(self.blocksize - 1))
        hb = max(lb, h & ~(self.blocksize - 1))

        print(l, lb, hb, h)
        hist = compute_hist(self.rdata, l, lb, self.n, self.s)
        blocks = self.blocks[lb // self.blocksize:hb // self.blocksize]
        if (lb < hb or hb == 0) and (hb < h):
            blocks.append(compute_hist(self.rdata, hb, h, self.n, self.s))

        # TODO compute binding grams
        for block in blocks:

            for k, v in block.items():
                hist[k] = hist.get(k, 0) + v

            lb += self.blocksize

        return hist

class bigrams(ngrams):
    n = 2

class trigrams(ngrams):
    n = 3


@jit(nopython=True)
def calc_entropy(data, s, shannon, hist, window, increments, decrements):
    ent = 0.0

    for i in range(data.shape[0]):

        v = data[i]

        o = window[i % s]
        window[i % s] = v

        fo = hist[v]
        f = fo + 1
        hist[v] = f
        ent += increments[fo]

        if i < s:
            continue

        fo = hist[o]
        f = fo - 1
        hist[o] = f
        ent += decrements[fo]

        shannon[i-s/2] = int(-ent / s / 8 * 255)

class shannon(identity):

    s = 128

    def set_data(self, data):
        assert len(data.shape) == 1

        print("Set data for %s (ignore next %s, its me.)" % (self, self.__class__.__name__))

        shannon = np.zeros(data.shape)

        sl = log(self.s, 2)

        # Instead of precomputing logs we should precompute freq changes.
        # This is easy to do, we only have self.s * 2 (up or down) changes.

        def logz(x):
            return log(x, 2) if x > 0 else 0

        increments = np.array([(i + 1) * (logz(i + 1) - sl) - i * (logz(i) - sl)
                               for i in range(self.s+2)])
        decrements = np.array([(i - 1) * (logz(i - 1) - sl) - i * (logz(i) - sl)
                               for i in range(self.s+2)])

        hist = np.zeros(256)
        window = np.zeros(self.s)


        calc_entropy(data, self.s, shannon, hist, window, increments, decrements)

        super().set_data(shannon)
