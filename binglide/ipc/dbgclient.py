import sys
import json
import shlex
import pprint
import asyncio
import argparse
import traceback

import zmq

from binglide import ipc
from binglide.ipc import dispatching, protocol, utils


class ClientDbg(protocol.Client):

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

        self.handle_cmd(shlex.split(cmd))
        self.prompt()

        # This is non blocking anyway. And it will handle the cases when the
        # socket became readable but the fd wasn't triggered because of
        # http://api.zeromq.org/4-0:zmq-getsockopt#toc24
        self.eventloop.call_soon(self.process_events)

    def handle_cmd(self, cmd):

        if not cmd:
            return

        key = "cmd_%s" % cmd[0]

        try:
            handler = self.dispatchtable[key][0]
        except (KeyError, IndexError):
            print("Unknown command %r." % cmd[0], file=sys.stderr)
            return

        parser = argparse.ArgumentParser(prog=cmd[0],
                                         description=handler.__doc__)

        try:
            handler(parser, cmd[1:])
        except SystemExit as e:
            if isinstance(e.code, str):
                print(e, file=sys.stderr)
        except Exception as e:
            print("%s" % (traceback.format_exc(),), end="", file=sys.stderr)

    def handle_report(self, service, reqid, body, data):
        print()
        print("got answer for %s, %r:" % (service, reqid))
        pprint.pprint(body)
        if data is not None:
            print("Attached data frame:\n%s" % data)
        self.prompt()

    @dispatching.bind()
    def on_cmd_help(self, parser, cmd):
        """List available commands."""

        for key, callbacks in self.dispatchtable.items():
            if not isinstance(key, str) or not key.startswith('cmd_'):
                continue
            print("%s\t - %s" % (callbacks[0].__name__[7:],
                                 callbacks[0].__doc__))

    @dispatching.bind()
    def on_cmd_meta(self, parser, cmd):
        """Display information about the current setup."""

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

    @dispatching.bind()
    def on_cmd_req(self, parser, cmd):
        """Issue a request to the network."""

        parser.add_argument("service")
        parser.add_argument("cmd", type=json.loads)
        args = parser.parse_args(cmd)

        reqid = self.request(args.service, args.cmd)
        print("request id: %s" % reqid)

    @dispatching.bind()
    def on_cmd_reqb(self, parser, cmd):
        """Issue a blocking request to the network."""

        parser.add_argument("service")
        parser.add_argument("cmd", type=json.loads)
        args = parser.parse_args(cmd)

        reqid, body = self.request_sync(args.service, args.cmd)
        print("request id: %s" % reqid)
        pprint.pprint(body)

    @dispatching.bind()
    def on_cmd_cancel(self, parser, cmd):
        """Cancel a request."""

        parser.add_argument("reqid")
        args = parser.parse_args(cmd)

        reqid = bytes(args.reqid, 'utf8')
        self.cancel(reqid)


class Main(utils.Main):

    def setup(self, parser):
        parser.add_argument("router", type=utils.ConnectSocket)

    def run(self, args):
        client = ClientDbg(self.zmqctx, args.router, 'binglide.ipc.dbgclient',
                           assertive=True, loglvl=self.loglvl)
        client.run()


if __name__ == '__main__':
    Main()
