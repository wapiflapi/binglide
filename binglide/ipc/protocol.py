#!/usr/bin/env python3
# -*- coding: utf-8 -*-

VERSION = b"BXMDP00"


def command(key):
    return VERSION + b"." + key


LIST = command(b"LIST")

REQUEST = command(b"REQUEST")
XREQUEST = command(b"XREQUEST")

CANCEL = command(b"CANCEL")
XCANCEL = command(b"XCANCEL")

REPORT = command(b"REPORT")
XREPORT = command(b"XREPORT")

READY = command(b"READY")
DISCONNECT = command(b"DISCONNECT")
