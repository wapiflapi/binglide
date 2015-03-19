"""
Backend infrastructure for binglide computations.
"""

from pprint import pprint

import circus

import binglide.config


def run(config):

    arbiter = circus.get_arbiter(config['server'])

    try:
        arbiter.start()
    finally:
        arbiter.stop()


def start(configfile=None):
    config = binglide.config.load_config(configfile)
    pprint(config)
    run(config)


def main():

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=argparse.FileType("r"))

    args = parser.parse_args()

    start(args.config)
