#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("broker")
    args = parser.parse_args()

    print(args)

    while True:
        print("Come Muscovite! Let the workers unite!")
        signal.pause()
