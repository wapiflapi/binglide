binwalk
=======

binwalk looking at ls, showing typical x86_64 bytecode.
The view is a trimensional represention of trigrams.
![binwalk looking at /bin/ls](http://i.imgur.com/yFbLstf.png)

binwalk looking at flower.bmp, showing typical patterns for a three channel image.
The view is a trimensional represention of trigrams.
![binwalk looking at /bin/ls](http://i.imgur.com/bc2c7HL.png)

binwalk looking at binwalk/gui.py, showing ascii data.
The view is a twodimensional represention of bigrams.
![binwalk looking at binwalk/gui.py](http://i.imgur.com/nuz103P.png)


binwalk looking at emacs23-nox.
This show the different parts of that file, the first one
looks like x86_64 bytecode. The second screenshot shows some data
that isn't imediatly recognizable, but does contain a lot of text.
![binwalk looking at emacs23-nox](http://i.imgur.com/oPuYAMV.png)
![binwalk looking at emacs23-nox](http://i.imgur.com/gIzVoIO.png)

## Requirements

   * PyQt4
   * pyqtgraph
   * numpy
   * numba

## Documentation

   Comming soon.

## Installation

   Detailed instructions comming soon, but install the requirements then:

   ```
   python3 setup.py intall
   ```
