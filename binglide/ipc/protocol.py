import sys
import json

import zmq

from binglide.ipc import messaging
from binglide.ipc import bodyfmt

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


class Peer(messaging.Node):

    def __init__(self, zmqctx, keyidx, logger, *args, **kwargs):
        super().__init__(zmqctx, zmq.DEALER, keyidx, logger,
                         *args, **kwargs)

    def encode_payload(self, payload):
        # FIXME: attrdict is not JSON encodable.
        # The dict() fix bellow is not good because it won't
        # work for nested dicts. We need a better solution.
        return bytes(json.dumps(dict(payload)), 'utf8')

    def decode_payload(self, payload):
        return json.loads(str(payload, 'utf8'),
                          object_hook=bodyfmt.BodyFmt)


class Client(Peer):

    def __init__(self, zmqctx, config, logger, *args, **kwargs):
        self.config = config
        super().__init__(zmqctx, 0, logger, *args, **kwargs)
        self.reqid = 0

    def wait_for_reqid(self, reqid):
        return self.wait_for(lambda m: m[2] == reqid)

    def request(self, service, body):

        self.reqid = self.reqid + 1

        service = bytes(service, 'utf8')
        reqid = bytes("%d" % self.reqid, 'utf8')
        body = self.encode_payload(body)

        msg = [REQUEST, service, reqid, b'', body]
        self.socket.send_multipart(msg)

        return reqid

    def request_sync(self, service, body):
        # FIXME: This needs a timeout because there is no garantee the network
        # will answer. Also there might be more than one answer, in that case
        # the user can continue to monitor reqid.

        thisreqid = self.request(service, body)
        key, msg = self.wait_for_reqid(thisreqid)
        service, reqid, body, data = self.parse_report(msg)
        return reqid, body, data

    def cancel(self, reqid, body=None):
        body = self.encode_payload({} if body is None else body)
        msg = [CANCEL, b'', reqid, b'', body]
        self.socket.send_multipart(msg)

    def list(self):
        self.socket.send_multipart([LIST])

    def list_sync(self):
        self.list()
        key, msg = self.wait_for_key(LIST)
        return [str(service, 'utf8') for service in msg[1:]]

    def parse_report(self, msg):
        # service, reqid, body, [data]
        data = None if len(msg) < 6 else msg[5]
        return str(msg[1], 'utf8'), msg[2], self.decode_payload(msg[4]), data

    @messaging.bind(REPORT)
    def on_report(self, msg):
        service, reqid, body, data = self.parse_report(msg)
        self.handle_report(service, reqid, body, data)


class Worker(Client):

    def __init__(self, zmqctx, config, *args, **kwargs):
        super().__init__(zmqctx, config, self.get_logger(), *args, **kwargs)
        self.canceledjobs = {}

    def __repr__(self):
        return self.servicename

    def get_logger(self):
        return 'binglide.server.workers.%s' % (self,)

    def get_service(self):
        return bytes(self.servicename, 'utf8')

    def start(self):
        super().start()
        self.ready()

    def ready(self):
        msg = [READY, self.get_service()]
        self.socket.send_multipart(msg)

    def get_ukey(self, meta):
        retaddr, reqid, clientid = meta
        return (reqid, clientid)

    def report(self, meta, body, data=None):
        retaddr, reqid, clientid = meta
        body = self.encode_payload(body)
        msg = [XREPORT, retaddr, reqid, clientid, body]
        if data is not None:
            msg.append(data)
        self.socket.send_multipart(msg)

    def check_canceled(self, meta):

        self.process_events()

        ukey = self.get_ukey(meta)
        return self.canceledjobs.pop(ukey, None)

    def handle_xcancel(self, meta, body):
        self.canceledjobs[self.get_ukey(meta)] = body

    @messaging.bind(XREQUEST)
    def on_xrequest(self, msg):
        _, retaddr, reqid, clientid, body = msg
        body = self.decode_payload(body)
        if self.handle_xrequest((retaddr, reqid, clientid), body):
            self.ready()

    @messaging.bind(XCANCEL)
    def on_xcancel(self, msg):
        _, retaddr, reqid, clientid, body = msg
        body = self.decode_payload(body)
        if self.handle_xcancel((retaddr, reqid, clientid), body):
            self.ready()

    @messaging.bind(DISCONNECT)
    def on_disconnect(self, msg):
        sys.exit(0)
