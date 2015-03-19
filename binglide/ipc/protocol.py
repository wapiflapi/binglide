import sys
import json

import zmq
import numpy
import attrdict

from binglide.ipc import messaging

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


class Payload(attrdict.AttrDict):
    pass


class Peer(messaging.Node):

    def __init__(self, zmqctx, keyidx, logger, *args, **kwargs):
        super().__init__(zmqctx, zmq.DEALER, keyidx, logger,
                         *args, **kwargs)

    def encode_payload(self, payload):

        data = []
        for i, array in enumerate(payload.get('attachments', [])):
            payload['attachments'][i] = {'dtype': str(array.dtype),
                                         'shape': array.shape}
            data.append(array)

        frames = [bytes(json.dumps(payload, default=dict), 'utf8')] + data
        return frames

    def decode_payload(self, frames):

        payload = json.loads(str(frames[0], 'utf8'), object_hook=Payload)

        attachments = payload.get('attachments', [])

        if len(attachments) != len(frames) - 1:
            self.logger.warn("number of attachments (%d) does not match "
                             "number of data frames (%d)." %
                             (len(attachments), len(frames) - 1))

        for i, (md, raw) in enumerate(zip(attachments, frames[1:])):
            array = numpy.frombuffer(raw, dtype=md.dtype)
            payload['attachments'][i] = array.reshape(md.shape)

        return payload

    def send(self, frames, **kwargs):
        self.socket.send_multipart(frames, **kwargs)


class Client(Peer):

    def __init__(self, zmqctx, config, logger, *args, **kwargs):
        self.config = config
        super().__init__(zmqctx, 0, logger, *args, **kwargs)
        self.reqid = 0

    def wait_for_reqid(self, reqid):
        return self.wait_for(lambda m: m[2] == reqid)

    def request(self, service, payload, **kwargs):

        self.reqid = self.reqid + 1

        service = bytes(service, 'utf8')
        reqid = bytes("%d" % self.reqid, 'utf8')
        frames = self.encode_payload(payload)

        msg = [REQUEST, service, reqid, b''] + frames
        self.send(msg, **kwargs)

        return reqid

    def request_sync(self, service, payload):
        # FIXME: This needs a timeout because there is no garantee the network
        # will answer. Also there might be more than one answer, in that case
        # the user can continue to monitor reqid.

        thisreqid = self.request(service, payload)
        key, msg = self.wait_for_reqid(thisreqid)
        service, reqid, payload = self.parse_report(msg)
        return reqid, payload

    def cancel(self, reqid, payload=None, **kwargs):
        frames = self.encode_payload({} if payload is None else payload)
        msg = [CANCEL, b'', reqid, b''] + frames
        self.send(msg, **kwargs)

    def list(self):
        self.send([LIST])

    def list_sync(self):
        self.list()
        key, msg = self.wait_for_key(LIST)
        return [str(service, 'utf8') for service in msg[1:]]

    def parse_report(self, msg):
        # service, reqid, payload
        payload = self.decode_payload(msg[4:])
        return str(msg[1], 'utf8'), msg[2], payload

    @messaging.bind(REPORT)
    def on_report(self, msg):
        service, reqid, payload = self.parse_report(msg)
        self.receive_report(service, reqid, payload)


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
        self.send(msg)

    def get_ukey(self, meta):
        retaddr, reqid, clientid = meta
        return (reqid, clientid)

    def report(self, meta, payload, **kwargs):
        retaddr, reqid, clientid = meta
        frames = self.encode_payload(payload)
        msg = [XREPORT, retaddr, reqid, clientid] + frames
        self.send(msg, **kwargs)

    def check_canceled(self, meta):

        self.process_events()

        ukey = self.get_ukey(meta)
        return self.canceledjobs.pop(ukey, None)

    def receive_xcancel(self, meta, payload):
        self.canceledjobs[self.get_ukey(meta)] = payload

    @messaging.bind(XREQUEST)
    def on_xrequest(self, msg):
        _, retaddr, reqid, clientid, *payload = msg
        payload = self.decode_payload(payload)
        if self.receive_xrequest((retaddr, reqid, clientid), payload):
            self.ready()

    @messaging.bind(XCANCEL)
    def on_xcancel(self, msg):
        _, retaddr, reqid, clientid, *payload = msg
        payload = self.decode_payload(payload)
        if self.receive_xcancel((retaddr, reqid, clientid), payload):
            self.ready()

    @messaging.bind(DISCONNECT)
    def on_disconnect(self, msg):
        sys.exit(0)
