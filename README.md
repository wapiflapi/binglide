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

   binglide has been developed in order to better understand the algoritms
   ressearched by [insert reference here]. The user interface is inspired
   by what was presented by ..Cantor.Dust.. presented at [XXX], but with
   no public release as of today.

   ### GUI Layout

   The main windows is split in three zones, the two on the left allow
   for selection of the part of the file that is being studied.
   The bigger pane on the right shows the results of the selected
   algorithm.


   ### Data visualisation (data)
   Data visualisation is the most basic of all views, it simply shows
   each byte as it is in the file by taking its value as a color, 0xff
   will be very bright, 0x00 will be black.

   ### Entropy visualisation (ent)
   This uses a sliding window over the data to compute "local" Shannon
   entropy. The color representes the entropy, if it is dark the data
   doesn't have high entropy, if it gets lighter the entropy increases.

   ### N-Gram visualisation (3G, 2G)
   This are the most useful views when it comes to identifying what kind
   of data one is looking at. The idea is to look at a histogram of
   bigrams or trigrams in the file. Those are represented in 2D or 3D.

   This representation ofers very visual patterns that are diferent
   enough from one data type to another to be easily recognized once
   you get used to them.

   A data point in one of those views represents how often thos bytes
   are found together. For example this is a 2D representation of the
   histogram of bigrams in a text file containing english text:

   ![binwalk looking at X](http://i.imgur.com/X.png)

   Notice the squares representing the lowercase ascii letters that
   follow eachother, notice also the smaller squares where uppercase
   is followed by lowercase or the oposite.

   Here are some reference data types:

   - bmp
   - wav

   "natural" data such as uncompressed images or sounds will have this
   diagonal shape, the image is composed of three channels (colors)
   that's why it has three separate "waves". Here is a greyscale image
   and one with a fourth channel for alpha:

   - greyscale
   - with alpha

   - x86_64
   - x86_32
   - arm

   bytecode also has a distinctive pattern, this is almost independent
   from the architecture. The architecture can be recognized but even
   unknown architzcture could be identified as bytecode.

   - random

   This is random data, encrypted data should look similar, compressed
   data however still offers some patterns:

   - deflate
   - pdf stuff



## Installation

   binglide uses python3, be careful to install packages for that
   version of python.

   This guide is for Linux distributions using the apt packet-manager, it
   shouldn't be hard to extrapolate what you need for other distributions.

   The basic libraries used by binglide are numpy and pyqtgraph.
   pyqtgraph needs pyqt4 and pyqt4.opengl, those can't be installed through
   pip as far as I know.

   ```
   apt-get install python3-pyqt4 python3-pyqt4.qtopengl
   pip3 install pyqtgraph numpy

   # In the root of the git directory:
   python3 setup.py intall
   ```

   However without the JIT optimisations this will be quite slow, for
   this the numba library is used
