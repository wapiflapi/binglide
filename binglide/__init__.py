
def main():

    import sys
    import argparse

    from PyQt4 import QtCore, QtGui

    import binglide.gui

    parser = argparse.ArgumentParser()
    parser.add_argument("file", default=None, nargs="?", type=argparse.FileType("rb"))
    args = parser.parse_args()

    app = QtGui.QApplication(sys.argv)

    binglideui = binglide.gui.BinglideUI()
    binglideui.show()

    if args.file is not None:
        binglideui.read_file(args.file)

    app.exec_()

    # This is a hack.
    # Letting the interpreter garbage collect will result in a segfault.
    # this is either PyQt or pyqtgraph's fault.
    import os
    os._exit(0)

