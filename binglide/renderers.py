  #!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

# Monkey patching fun.
# Set the color.
def LinearRegionItem_paint(self, p, *args):
    profiler = pg.debug.Profiler()
    pg.UIGraphicsItem.paint(self, p, *args)
    p.setBrush(self.currentBrush)
    p.setPen(pg.mkPen(color="8833FF", width=5))
    p.drawRect(self.boundingRect())
pg.LinearRegionItem.paint = LinearRegionItem_paint


class Renderer(object):

    dim = None
    known_levelers = set()
    known_painters = set()
    known_mixers = set()
    known_projectors = set()

    @classmethod
    def get_known(cls, what, src):
        for f, limits in what:

            if limits is None:
                yield f
                continue

            if callable(limits):
                if limits(cls.dim, src):
                    yield f
                continue

            if isinstance(limits[0], (tuple, list)):
                if src not in limits[0]:
                    continue
            else:
                if src != limits[0]:
                    continue

            if isinstance(limits[1], (tuple, list)):
                if src not in limits[1]:
                    continue
            else:
                if src != limits[1]:
                    continue

            yield f


    @classmethod
    def register_leveler(cls, limits):
        def decorator(p):
            cls.known_levelers.add((p, limits))
            # print("Registered leveler %s to %s" % (p, limits))
            return p
        return decorator

    @classmethod
    def get_levelers(cls, src):
        yield from cls.get_known(cls.known_levelers, src)

    @classmethod
    def register_painter(cls, limits):
        def decorator(p):
            cls.known_painters.add((p, limits))
            # print("Registered painter %s to %s" % (p, limits))
            return p
        return decorator

    @classmethod
    def get_painters(cls, src):
        yield from cls.get_known(cls.known_painters, src)

    @classmethod
    def register_mixer(cls, limits):
        def decorator(p):
            cls.known_mixers.add((p, limits))
            # print("Registered mixer %s to %s" % (p, limits))
            return p
        return decorator

    @classmethod
    def get_mixers(cls, src):
        yield from cls.get_known(cls.known_mixers, src)

    @classmethod
    def register_projector(cls, limits):
        def decorator(p):
            cls.known_projectors.add((p, limits))
            # print("Registered projector %s to %s" % (p, limits))
            return p
        return decorator

    @classmethod
    def get_projectors(cls, src):
        yield from cls.get_known(cls.known_projectors, src)

    def __init__(self, region=False):

        self.calc = None
        self.leveler = None
        self.painters = {}
        self.projector = None

        self.forwards = []
        self.region = None

        self.needs_region = region

        self.lvls = 1.0

    def forward(self, other):
        self.forwards.append(other)

    def set_region(self, low, high):
        # TODO: we should always have a calc, add it to init.

        if self.calc is not None:
            self.calc.set_region(low, high)
        self.do_update()
        self.region_update()

    def set_calc(self, calc):
        self.calc = calc

    def set_leveler(self, leveler):
        self.leveler = leveler

    def set_projector(self, projector):
        self.projector = projector

    def rst_painters(self):
        self.painters = {}

    def add_painter(self, painter, *mixers):
        painter = self.painters.setdefault(painter, set())
        for m in mixers:
            painter.add(m)

    def del_painter(self, painter):
        self.painters[painter].remove(mixer)

    def do_update(self):

        print("Updating %s" % self)

        if self.calc is None:
            print("\tskiping because calc == None")
            return


        data = self.calc.get_data()
        if data is None:
            print("\tskiping because %s data == None" % self.calc)
            return

        ddim = self.calc.get_ddim()
        ratio = self.get_ratio()

        # Ignore stupid resizes.
        # if any(x < 10 for x in ratio):
        #     print("Ignored update.");
        #     return

        if self.leveler is None:
            try:
                leveler = next(self.get_levelers(ddim))
            except StopIteration:
                print("No suitable leveler found %s -> %s." % (ddim, self.dim))
                return
            self.set_leveler(leveler)

        if not self.painters:
            try:
                painter = next(self.get_painters(ddim))
                mixer = next(self.get_mixers(ddim))
            except StopIteration:
                print("No suitable mixer found %s -> %s." % (ddim, self.dim))
                return
            self.add_painter(painter, mixer)

        if self.projector is None:
            try:
                projector = next(self.get_projectors(ddim))
            except StopIteration:
                print("No suitable projector found %s -> %s." % (ddim, self.dim))
                return
            self.set_projector(projector)

        if len(data) == 0:
            print("Warning: 0-length data.")
            return

        leveled = self.leveler(self.dim, data, self.calc.get_shape())
        colored = np.zeros(leveled.shape + (4,), dtype=np.uint8)

        channels = (mixer.get_coefs() for mixers in self.painters.values() for mixer in mixers)
        channels = (sum(nbs) for nbs in zip(*channels))
        coefs = [1/n if n != 0 else 0 for n in channels]

        # Be nice with alpha.
        if coefs[3] == 0:
            colored[..., 3] = 255

        print("coefs= %s" % (coefs, ))
        for painter, mixers in self.painters.items():
            colored = painter(colored, leveled, mixers, coefs)

        # print("Projecting %s -> %s using %s." % (self.ddim, self.dim, self.projector))
        self.projected = self.projector(self.dim, colored, ratio)

        # print("Rendering %s." % (self.projected.shape,))
        self.do_render(self.projected)


    def rescale(self, projected):
        print(self.lvls)
        return np.minimum(projected.astype(int) * self.lvls, 255)

    def setup_region(self):
        self.region = None

    def setlvl(self, lvl):
        self.lvls = lvl

    def region_update(self):
        if not self.forwards:
            return
        raise NotImplementedError("Renderee doesnt support regions.")

    def region_full(self):
        return

class Renderer2D(pg.GraphicsLayoutWidget, Renderer):
    """
    """

    dim = "2D"

    def __init__(self, parent=None, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        super().__init__(parent)
        self.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.ci.layout.setSpacing(0)

        self.view = self.addViewBox()
        # self.view.setAspectLocked(True)
        self.view.setAspectLocked(lock=False)

        self.view.invertY(True)

        self.view.setContentsMargins(0, 0, 0, 0)

        self.img = pg.ImageItem(border='w')
        self.view.addItem(self.img)

        self.live_region = False

        if self.needs_region:
            self.setup_region()

        self.show()

    def setup_region(self):
        self.region = pg.LinearRegionItem(orientation=pg.LinearRegionItem.Horizontal)
        self.view.addItem(self.region, ignoreBounds=True)
        self.region.sigRegionChangeFinished.connect(self.region_update)
        self.region.sigRegionChanged.connect(self.region_changed)
        self.needs_region = False

    def region_changed(self):
        if self.live_region:
            self.region_update()

    def region_update(self):

        if self.region is None:
            return

        if not self.forwards:
            return

        low, high = self.region.getRegion()

        shape = self.calc.get_shape() + (4,) # RGBA.
        low = self.projector.lookup(shape, self.projected.shape, (0, low))
        high = self.projector.lookup(shape, self.projected.shape, (0, high))

        # Now that we are in our data coordinates we need to be in global data.
        low = self.calc.lookup(low)
        high = self.calc.lookup(high)

        for f in self.forwards:
            f.set_region(low, high)

    def region_full(self):
        if self.region:
            self.region.setRegion([0, self.projected.shape[1]])

    def lock(self):
        self.view.setMouseEnabled(False, False)

    def get_ratio(self):
        geom = self.view.screenGeometry()
        w, h = geom.width(), geom.height()
        return w, h

    def do_render(self, projected):
        projected = self.rescale(projected)

        self.img.setImage(projected, levels=[10, 10])

        for _ in (1, 2): # No idea why but need to do this twice.
            self.view.setRange(xRange=(0, self.projected.shape[0]),
                               yRange=(0, self.projected.shape[1]),
                               padding=0.0)

        if self.region:
            self.region.setBounds([0, self.projected.shape[1]])


class Renderer3D(gl.GLViewWidget, Renderer):
    """
    """

    dim = "3D"

    def __init__(self, parent=None, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        super().__init__(parent)

        self.plot = None
        self.show()

    def get_ratio(self):
        # TODO: ignore stupid resizes by returning small value.
        return 256, 256, 256

    def do_render(self, projected):
        projected = self.rescale(projected)

        x, y, z, _ = projected.shape
        print(x, y, z)
        d = float(max(x, y, z) * 2)

        if self.plot is None:
            self.plot = gl.GLVolumeItem(projected, smooth=False)
            self.addItem(self.plot)
            self.axis = gl.GLAxisItem(glOptions="opaque")
            self.addItem(self.axis)
            self.opts['distance'] = self.distance = d
        else:
            # Latest version has .setData but is not in PyPi
            self.plot.data = projected
            self.plot.initializeGL()

        ratio = d / self.distance

        self.opts['distance'] *= ratio
        self.distance = d

        self.plot.resetTransform()
        self.plot.translate(-x/2, -y/2, -z/2)

        self.axis.setSize(x, y, z)
        self.axis.resetTransform()
        self.axis.translate(-x/2, -y/2, -z/2)

# Give projectors a chance to register.
from binglide import levelers, projectors, painters, mixers, calcs
