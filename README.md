binwalk
=======

binwalk is a visual reverse engineering tool. It is designed to offer a quick overview of the different data types that are present in a file. The screenshot bellow shows a small portion of the php5 binary that has a weird signature pattern:

![binwalk looking at php5](http://i.imgur.com/O6HMfSn.png)

## Requirements

   * PyQt4
   * pyqtgraph
   * numpy
   * numba


## Installation

binglide uses python3, be careful to install packages for that version of python.

This guide is for Linux distributions using the apt packet-manager, it shouldn't be hard to extrapolate what you need for other distributions We just need to get all the requirements working and then setup binglide using setup.py.

The basic libraries used by binglide are numpy and pyqtgraph. pyqtgraph needs pyqt4 and pyqt4.opengl, these can't be installed through pip as far as I know.

```
apt-get install python3-pyqt4 python3-pyqt4.qtopengl
pip3 install pyqtgraph numpy

# In the root of the git directory:
python3 setup.py intall
```

However without the JIT optimisations this will be quite slow, for this the numba library is used. https://github.com/numba/numba


## Documentation

binglide has been developed in order to better understand some of the algoritms used by [Cantor dust](https://sites.google.com/site/xxcantorxdustxx/).

### GUI Layout
The main windows is split in three zones, the two on the left allow for selection of the part of the file that is being studied. The bigger pane on the right shows the results of the selected algorithm.

### Data visualisation (data)
Data visualisation is the most basic of all views, it simply shows each byte as it is in the file, taking its value as a color: 0xff will be very bright, 0x00 will be black.

### Entropy visualisation (ent)
This uses a sliding window over the data to compute "local" Shannon entropy. The color represents the entropy, if it is dark then the data doesn't have high entropy, if it gets lighter the entropy increases.

### N-Gram visualisation (3G, 2G)
This are the most useful views when it comes to identifying what kind of data one is looking at. The idea is to look at a histogram of bigrams or trigrams in the file. Those are represented in 2D or 3D.

This representation ofers very visual patterns that are diferent enough from one data type to another to be easily recognized once you get used to them.

A data point in one of those views represents how often those bytes are found together. For example this is a 2D representation of the histogram of bigrams in english text:

![binwalk looking at english text](https://raw.githubusercontent.com/wapiflapi/binglide/master/samples/text_2g.png)

Notice the square representing the lowercase ascii letters that follow each other. Slightly to the left we see some traces of uppercase followed by lowercase and beneath that another, more subtle, square representing all caps words. The rest is mainly characters followed by spaces or other punctuation.

## Sample data types

You can find screenshots of some common data types under the /samples/ directory.
