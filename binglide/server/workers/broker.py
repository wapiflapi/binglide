import collections

import zmq

from binglide.ipc import messaging, protocol, utils


class KeyDefaultDict(collections.defaultdict):

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        return self.setdefault(key, self.default_factory(key))


class RoundRobin(object):

    def __init__(self):

        self.clients = KeyDefaultDict(self.add_client)
        self.queue = collections.deque()

    def add_client(self, client):
        client_queue = collections.deque()
        self.queue.append((client, client_queue))
        return client_queue

    def add(self, client, task):
        self.clients[client].append(task)

    def pop(self):

        client, client_queue = self.queue.popleft()

        task = client_queue.popleft()

        if client_queue:
            self.queue.append((client, client_queue))
        else:
            self.clients.pop(client)

        return client, task


class GreedySetDict(collections.defaultdict):

    def __init__(self):
        super().__init__(set)

    def popfrom(self, key, *args):

        value = self[key].pop(*args)
        if not self[key]:
            del self[key]
        return value

    def removefrom(self, key, *args):

        value = self[key].remove(*args)
        if not self[key]:
            del self[key]
        return value


class Broker(messaging.Node):

    def __init__(self, zmqctx, config, *args, **kwargs):
        self.config = config
        super().__init__(zmqctx, zmq.ROUTER, 1,
                         'binglide.server.broker', *args, **kwargs)

        self.requests = collections.defaultdict(RoundRobin)

        self.workers = {}
        self.services = GreedySetDict()
        self.idleworkers = GreedySetDict()
        self.activeworkers = {}
        self.jobs = GreedySetDict()

    def issue_work(self, worker, task):

        task[2] = task[0]
        task[1] = protocol.XREQUEST
        task[0] = worker

        job = (task[3], task[4])

        self.jobs[job].add(worker)
        self.activeworkers[worker] = job
        self.socket.send_multipart(task)

    def match_worker(self, service):

        if service not in self.idleworkers:
            return

        try:
            client, task = self.requests[service].pop()
        except IndexError:
            return

        # shouldn't fail because service has entries.
        worker = self.idleworkers.popfrom(service)
        self.issue_work(worker, task)

    @messaging.bind(protocol.LIST)
    def on_list(self, msg):
        reply = [msg[0], protocol.LIST] + list(self.services)
        self.socket.send_multipart(reply)

    @messaging.bind(protocol.REQUEST)
    def on_request(self, msg):

        if not msg[4]:
            # This client is the original client.
            msg[4] = msg[0]

        self.requests[msg[2]].add(msg[4], msg)

        # We need to match in case there is already a worker waiting.
        self.match_worker(msg[2])

    @messaging.bind(protocol.CANCEL)
    def on_cancel(self, msg):

        if not msg[4]:
            # This client is the original client.
            msg[4] = msg[0]

        job = (msg[3], msg[4])

        for worker in self.jobs[job]:

            msg[2] = msg[0]
            msg[1] = protocol.XCANCEL
            msg[0] = worker

            self.socket.send_multipart(msg)

    @messaging.bind(protocol.READY)
    def on_ready(self, msg):

        self.workers[msg[0]] = msg[2]
        self.services[msg[2]] = msg[0]
        self.idleworkers[msg[0]] = msg[2]
        self.idleworkers[msg[2]].add(msg[0])
        try:
            job = self.activeworkers.pop(msg[0])
            self.jobs.removefrom(job, msg[0])
        except KeyError:
            pass

        # We need to match in case there is already a task waiting.
        self.match_worker(msg[2])

    @messaging.bind(protocol.XREPORT)
    def on_xreport(self, msg):

        service = self.idleworkers[msg[0]]

        msg[0] = msg[2]
        msg[1] = protocol.REPORT
        msg[2] = service

        self.logger.debug("forwarding report: %s" % msg)
        self.socket.send_multipart(msg)

    @messaging.bind(protocol.DISCONNECT)
    def on_disconnect(self, msg):

        service = self.workers.pop(msg[0])
        self.services.removefrom(service, msg[0])

        try:
            self.idleworkers.removefrom(service, msg[0])
        except KeyError:
            pass

        try:
            job = self.activeworkers.pop(msg[0])
            self.jobs.removefrom(job, msg[0])
        except KeyError:
            pass


class Main(utils.Main):

    runnable = Broker

    def setup(self, parser):
        parser.add_argument("router", type=utils.BindSocket)


if __name__ == '__main__':
    Main()
