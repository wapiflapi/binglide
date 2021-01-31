#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from binglide.renderers import Renderer

class ChannelMixer(object):

    def __init__(self, reds=False, greens=False, blues=False, alpha=False):
        self.channels = [i for i, v in enumerate((reds, greens, blues, alpha)) if v]

    def get_coefs(self):
        return [float(c in self.channels) for c in range(4)]

    def __call__(self, colored, data, coefs):
        for c in self.channels:
            colored[..., c] = colored[..., c] + (data * coefs[c])

mix_greys = Renderer.register_mixer(None)(
    ChannelMixer(True, True, True))
mix_reds = Renderer.register_mixer(None)(
    ChannelMixer(reds=True))
mix_greens = Renderer.register_mixer(None)(
    ChannelMixer(greens=True))
mix_blues = Renderer.register_mixer(None)(
    ChannelMixer(blues=True))
mix_alpha = Renderer.register_mixer(None)(
    ChannelMixer(alpha=True))
