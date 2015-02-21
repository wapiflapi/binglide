#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import shlex
import asyncio

import zmq

from binglide import ipc
from binglide.ipc import utils


class ClientDbg(utils.Client):

    def run(self):
        self.eventloop = asyncio.get_event_loop()

        sockfd = self.socket.get(zmq.FD)
        self.eventloop.add_reader(sockfd, self.process_events)
        self.eventloop.add_reader(sys.stdin, self.on_stdin)

        self.prompt()

        self.eventloop.run_forever()

    def prompt(self, prompt=">>> "):
        sys.stdout.write(prompt)
        sys.stdout.flush()

    def on_stdin(self):
        cmd = sys.stdin.readline()
        if not cmd:
            sys.exit()

        cmd = shlex.split(cmd)

        if cmd:
            try:
                self.dispatch("cmd_%s" % cmd[0], cmd)
            except NotImplementedError as e:
                print("Unknown command %r (%s)." % (cmd[0], e), file=sys.stderr)

        self.prompt()

    @utils.bind()
    def on_cmd_meta(self, cmd):

        def header(title, width=80):
            print((" %s " % title).center(width, '='))

        def footer():
            pass

        header("client info")
        print("socket    : %s" % self.config)
        footer()

        header("components versions")
        for lib, version in ipc.versions().items():
            print("%-10s: %6s" % (lib, version))
        footer()

        header("network capabilities")
        print("requesting service LIST...", end="\r")
        servicelist = self.list_sync()
        print("services  : %s" % ", ".join(servicelist), end="\033[K\n")
        footer()

    def handle_report(self, service, reqid, body):
        self.logger.info("got answer for %s, %r" % (service, reqid))



class Main(utils.Main):

    def setup(self, parser):
        parser.add_argument("router", type=utils.ConnectSocket)

    def run(self, args):
        client = ClientDbg(self.zmqctx, args.router, 'binglide.ipc.dbgclient',
                           assertive=True, loglvl=self.loglvl)
        client.run()


if __name__ == '__main__':
    Main()
