import numpy as np
import pyqtgraph as pg

from PyQt4 import QtCore, QtGui

from binglide import renderers, levelers, projectors, painters, mixers, calcs

class BinglideUI(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = None
        self.calc = None

        self.calc_trigrams = calcs.trigrams()
        self.calc_bigrams = calcs.bigrams()
        self.calc_entropy = calcs.shannon()
        self.calc_data = calcs.identity()

        self.calc_data_s1 = calcs.identity()
        self.calc_data_s2 = calcs.identity()

        self.initUI()

    def trigram_mode(self):
        view = self.set_view3D()
        view.set_calc(self.calc_trigrams)
        view.set_leveler(levelers.lvl_cumul256proj_NDS)
        view.set_projector(projectors.proj_identity)

        view.rst_painters()
        view.add_painter(painters.paint_values, mixers.mix_blues)
        view.add_painter(painters.paint_values, mixers.mix_alpha)
        view.add_painter(painters.paint_asciiposx, mixers.mix_reds)

        self.do_update()

    def bigram_mode(self):
        view = self.set_view2D()
        view.set_calc(self.calc_bigrams)
        view.set_leveler(levelers.lvl_cumul256proj_NDS)
        view.set_projector(projectors.proj_identity)

        view.rst_painters()
        view.add_painter(painters.paint_values, mixers.mix_blues)
        view.add_painter(painters.paint_asciiposx, mixers.mix_reds)

        view.view.invertY(False)

        self.do_update()

    def entropy_mode(self):
        view = self.set_view2D()
        view.set_calc(self.calc_entropy)

        view.set_leveler(levelers.lvl_clip)

        view.set_projector(projectors.proj_scanline)

        view.rst_painters()
        view.add_painter(painters.paint_values, mixers.mix_greens)

        view.view.invertY(True)

        self.do_update()

    def data_mode(self):
        view = self.set_view2D()
        view.set_calc(self.calc_data)

        view.set_leveler(levelers.lvl_clip)

        view.set_projector(projectors.proj_scanline)

        view.rst_painters()
        view.add_painter(painters.paint_values, mixers.mix_blues)
        view.add_painter(painters.paint_ascii, mixers.mix_reds)

        view.view.invertY(True)

        self.do_update()

    def live_region(self, checked):
        self.scale1.live_region = checked
        self.scale2.live_region = checked
        self.levels.setTracking(checked)

    def change_levels(self, value):

        value = value / 50

        self.view2D.setlvl(value)
        self.view3D.setlvl(value)
        self.do_update()

    def view_all(self):
        self.scale1.region_full()
        self.scale2.region_full()

    def read_file(self, f):
        self.data = np.fromstring(f.read(), dtype='uint8')
        self.update_data()
        self.view_all()

    def open_file(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
        with open(fname, 'rb') as f:
            self.read_file(f)

    def update_data(self):
        if self.data is None:
            return

        # update scale1 & 2
        self.calc_data.set_data(self.data)
        self.calc_entropy.set_data(self.data)
        self.calc_bigrams.set_data(self.data)
        self.calc_trigrams.set_data(self.data)

        self.calc_data_s1.set_data(self.data)
        self.calc_data_s2.set_data(self.data)

        # Use calc to update view.
        print("Data is set, update!")
        self.do_update()

    def set_view3D(self):
        self.activeView = view = self.view3D
        self.scale2.forwards = [view]
        self.view.setCurrentWidget(view)
        return view

    def set_view2D(self):
        self.activeView = view = self.view2D
        self.scale2.forwards = [view]
        self.view.setCurrentWidget(view)
        return view

    def initUI(self):
        self.setWindowTitle('binglide')

        toolbar = QtGui.QToolBar()
        self.toolbar = toolbar


        modeGroup = QtGui.QActionGroup(self);

        trigramAction = QtGui.QAction('3G', self)
        trigramAction.setShortcut('3')
        trigramAction.triggered.connect(self.trigram_mode)
        trigramAction.setCheckable(True)
        toolbar.addAction(trigramAction)
        modeGroup.addAction(trigramAction)

        bigramAction = QtGui.QAction('2G', self)
        bigramAction.setShortcut('2')
        bigramAction.triggered.connect(self.bigram_mode)
        bigramAction.setCheckable(True)
        toolbar.addAction(bigramAction)
        modeGroup.addAction(bigramAction)

        entropyAction = QtGui.QAction('ent', self)
        entropyAction.setShortcut('e')
        entropyAction.triggered.connect(self.entropy_mode)
        entropyAction.setCheckable(True)
        toolbar.addAction(entropyAction)
        modeGroup.addAction(entropyAction)

        dataAction = QtGui.QAction('data', self)
        dataAction.setShortcut('d')
        dataAction.triggered.connect(self.data_mode)
        dataAction.setCheckable(True)
        toolbar.addAction(dataAction)
        modeGroup.addAction(dataAction)

        dataAction.setChecked(True)

        spacer = QtGui.QWidget()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        self.levels = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.levels.setRange(0, 400)
        self.levels.setValue(50)
        self.levels.setTracking(False)
        self.levels.valueChanged.connect(self.change_levels)
        toolbar.addWidget(self.levels)

        liveRegion = QtGui.QAction('live', self)
        liveRegion.setShortcut('l')
        liveRegion.toggled.connect(self.live_region)
        liveRegion.setCheckable(True)
        toolbar.addAction(liveRegion)

        allAction = QtGui.QAction('all', self)
        allAction.setShortcut('a')
        allAction.triggered.connect(self.view_all)
        toolbar.addAction(allAction)

        openFile = QtGui.QAction('open', self)
        openFile.setShortcut('o')
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.open_file)
        toolbar.addAction(openFile)

        exitAction = QtGui.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)

        self.addToolBar(toolbar)

        w = QtGui.QWidget()
        self.setCentralWidget(w)
        grid = QtGui.QGridLayout()
        w.setLayout(grid)

        grid.setSpacing (0);
        grid.setContentsMargins (0, 0, 0, 0);

        self.scale1 = scale1 = renderers.Renderer2D(self, region=True)
        self.scale2 = scale2 = renderers.Renderer2D(self, region=True)

        self.view = QtGui.QStackedWidget()
        self.view2D = renderers.Renderer2D(self)
        self.view3D = renderers.Renderer3D(self)

        self.view.addWidget(self.view2D)
        self.view.addWidget(self.view3D)

        self.activeView = None

        scale1.sizeHint = lambda: QtCore.QSize(150, 700)
        scale2.sizeHint = lambda: QtCore.QSize(150, 700)
        self.view.sizeHint = lambda: QtCore.QSize(700, 700)

        grid.addWidget(scale1, 0, 0)
        grid.addWidget(scale2, 0, 1)
        grid.addWidget(self.view, 0, 2)

        scale1.lock()
        scale2.lock()

        scale1.forward(scale2)

        scale1.set_calc(self.calc_data_s1)
        scale1.set_leveler(levelers.lvl_clip)
        scale1.add_painter(painters.paint_values, mixers.mix_greys)

        scale2.set_calc(self.calc_data_s2)
        scale2.set_leveler(levelers.lvl_clip)
        scale2.add_painter(painters.paint_values, mixers.mix_greys)

        self.data_mode()

    def do_update(self, regions=True):
        print("Updating %s" % self)
        self.scale1.do_update()
        self.scale2.do_update()
        if regions:
            # TODO: shouldn crash.
            try:
                self.scale2.region_update()
            except:
                pass
        if self.activeView is not None:
            self.activeView.do_update()

    def resizeEvent(self, *args, **kwargs):
        print("Resize event...")
        super().resizeEvent(*args, **kwargs)
        self.do_update(regions=False)
