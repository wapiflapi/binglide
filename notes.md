
This documents contains some random notes that aren't part of the documentation,
but that I want to keep track of for later development.

## Ideas for the GUI.

For the QT/zmq integration we probably want to use this:
- http://qt-project.org/doc/qt-4.8/qsocketnotifier.html
- http://api.zeromq.org/2-1:zmq-getsockopt#toc19


I don't think binglide.ipc should be concerned by this. Lets just provide a
decent API, and keep in mind it will need to be integrated using the above in
the GUI.



## Random thoughts about the cache

We can either use "provider cache" where an accessor object returns cached
results, or use a "requester cache" where an object performing a request first
checks the cache (through a helper). The second option is more flexible, since
we often won't have the accessor object, or we'd need proxies and stuff, or we'd
need to send cached stuff over the network instead of accessing it?

What I just said is probably wrong. Provider Cache is the clean solution I
think. So what if we send stuff over the network. Shouldn't be *that* slow, we
where going to send it anyway if it wasnt cached. And this way we (somewhat)
handle distributed caches.

If we do it like that Accessors need to be cache aware. And so should Workers,
in some ways they are a special case of Accessors.

Basically we need a Requestable mixin which provides an interface similar to the
API. Should work for both workers and DDA (Direct Data Access).

Lets have dedicated workers handling DDA.
