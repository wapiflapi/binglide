
This document isn't up to date. It purpose was to explain the design decisions
being taken for the multiprocessing and IPC architecture of binglide v2.

# Synopsis

The main idea that this document ends up advocating is to have N workers for
each type of service. In this scenario each worker knows how to do only one
task. Those workers receive tasks from the broker who is responsable for
splitting jobs into smaller tasks accoring to the cache. This endsup being hard
to implement because it needs to do a lot of bookeeping to know what data it
should forward to what services and who to notify for cancelations.

see comments in mdp/mdp.py (if still relevant at the time of reading)

if workers could act as clients and request the chunks they need themselves this
problem would be solved. for workers to act as clients there are two options:

  1. active waiting
  2. Avoid loops. (This requires well behaved workers or bookeeping.)

In both cases workers can act as clients, how this is implemented (option 1 or
2) isn't relavant and can even be changed later on. Its probably best to start
with (2) and implement (1) if its needed one day.

In both cases we could either delagate stuff to dedicated service that knows
about the cache and splits work, or we could have some helper routines in a
library that do this. Of course its also always an option to have the workers do
the splitting themself if they want to.

For cancelations we probably want a global job id wich is (clientid, reqid).
The problem is this won't match subrequests since there clientid will be the
original worker because he is the one expecting the reply. One could argue that
worker could set its reqid to the global id but thats not possible, the broker
doesnt know if that was on purpose or not.

We need job id and task id. job id is *only* set when receiving a request from a
real client (if not already set!). And task id is set by each client (and
workers) for example: `jobid = "%d:%s%s" % (len(cid), cid, rid)`

### This should work. Shouldn't it?
When canceling a client gives an empty job id, and it will be calculated the
same way as when it was first choosen. Then all workers working on that job will
be told to cancel.


# Goals

We want something where a client can issue a request and receives multiple
answers because a first quick answer might come from cache while a more detailed
answer is being computed.

Each request can be computed in parallel because it can be devided in chunks, it
needs to be agregated before it can be sent back to the client.

Requests should be able to be canceled by a client before they are finished.

Right now we have the need to compute histogram data on large files with cache
support. This can work great by having a reducer process agregating results from
mappers. this works because we have one type of reducer and one type of mapper
with a minimum map/reduce ratio among the workers.

What happens if in the future we need something like A <- B <- C. This will
require at least three processes with two of them waiting. We need to make sure
we can't have all processes waiting and none computing. How do we provide a
garentee for this?

Can a reducer provide a list of requirements before-hand? Does that solve our
problem? It doesnt solve it since the reducer will still need to be agregating
stuff. NOT A SOLUTION


# Active waiting

Another option is to not have reducing doing nothing while waiting. They should
be computing the stuff they need themselves. At least this way even if no one is
helping stuff will get done.

Careful not to accumulate to much incoming data while doing so. We should have a
stack of tasks being processed. Do we need to check incoming for N+1 when
cheking notifications in N? -> Yes. because we need to know about
cancelations. Also recursive cancelations WTF. My brain hurts.

# Independant workers


Most of the complexity in the previous documents originated in the wish to be
able to have a arbitrary limited amount of worker processes. This was done so
the user could be sure that a only a maximum number of cores where used. By
dropping this requirement, and maybe relying on core affinities later on, we can
drastically simplify the architecture. First this allows us to have
single-purpose workers that can be implemented in any language.

* futures with "then"? @k4nar.

* talk about latest designs and iterations. The v1 -> v5 ?

Basically we truely have a MDM v2 but with added notification to support
cancelations. This is basically PUB/SUB embededed in the asyn dealer/router
setup just like what is done for heartbeats or disconnections. We can either
tell everyone to cancel a specific job idea with workers doing the filtering
(1), or the broker can choose to only warn the right workers (2). Probably the
right thing to do here is to mandate 1 and make 2 optional and implementation
dependent. It doesnt matter much except for congestion issues on the asyn
network.


# Reliability

TODO: update this section with newest design. We can intengrate this stuff into
the design and iteration process of the previous versions if relevant.

* pub-sub: If a client dies we dont care, he doesnt need the notifications
  anymore. If server dies we have a bigger problem.

* pipeline: If the collector (client/sink) doesn't get an answer in a reasonable
  amount of time he can re-issue the request.

  - If a client re-issues a request the venitlator will see the chunks as being
  processed already. In that case there should be a timestamp on that in-process
  and if it has been to long the ventilator can restart those tasks.

  - This job could also be done by the sink if waiting for some requests to
  complete for too long. The question is should they both do it or not?

Types of failure we aim to handle: worker crashes and restarts, worker busy
looping, worker overload, queue crashes and restarts, and network disconnects.


# Implementation

Having workers handle only one service makes them a lot easier to implement. For
python based workers we can have a base class implementing the BXMDMv2 protocol.

We do need to define service level protocols with a common base for file access
and cache management. We probably need to define a format for matrix
transmissions but can simply be numpy's.

# Cache awareness

The cache serves to accelarate computations by re-using past results. The
problem we have is that we do not expect to have identical requests issued
multiple times. Therefor it is pointless to cache those results exactly.

However because most requests can, and will, be split up in several chunks we
can cache the results for thos since they can be the same if we make them. (eg:
align them on block boundary and have them have the same size.)


* We need cache awareness in two places:
  - Broker: should know what chunks still need to be mapped.
	- Mapper: should know what/when to agregate.

  1. An alternative would be for the broker to forward all computed data to
  the mappers even if that means reading from disk in the broker.

  2. Other alternative is the mapper tells the brokers the chunks it needs but
  that forces us to have a mapper running which we don't want in some cases.

* What happens if we have a request that shouldn't be cached? How do we
  transfer data? This sucks and pushes for option (1).


## Dynamic block sizes

If a request is smaller than the block size it won't profit from it. On the
other hand if a request is way bigger there will be a lot of agregation to do.

We probably want to have something like for a request try to split it in e.g 10
and re-split those in 10 requests etc. This way it should generate caches
suitable for the type of requests that are made at those locations. The question
is how many times we should recursively split. Two options: (1) until we have a
min-size for the mappers, or (2) a fixed amount of time.

  1. Problem with this is that it generates a lot of cache files and takes a
     huge amount of place in storage.

  2. This generates less re-usable cache (for smaller requests) and if we had an
     unlimited ammount of workers this wouldnt scale optimally.

Maybe a solution would be (1) with an option not to commit results to disk but
still spliting work for the workers until min-size. But then we loose time in
the brokers. So maybe mix between (1) and (2)

>We won't do active waiting at first. This means workers should make calls to
>the same service type or we are at risk of dead locking. This is the main
>limitation.

This meas we can't do recurseive cache splitting. The broker will need to do the
work. We do need to decide what levels we will cache though. We probably want to
have something like 10% size of the request for future speed ups in similar
requests. But the question we need to answer is how many smaller chunks we want
to commit to disk as well why we are computing anyway. This is hard to
answser. It depends a lot of the future small requests at this place that we
cant really predict. However the larger caches should allow for fast replies on
the smaller ones regardless of the achieved accuracy. I this enough? We probably
want two levels though. Something like 10% and 1% if relevant. (check min size
off course.)


# insight on number of workers

The ideal chunk size for splitting a request is the total size divided by the
number of available workers.

The ideal size for chunks being cached to disk depends on the request patterns
and which will be the sizes of future requests in this location.


    <ressource>.<part>
    HIST_file1hash.1024_2048
    DIFF_file1hash_file2hash.0_4096
	ENT_file1hash.1024_2048

