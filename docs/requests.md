
A request made to the backend should have a standard format that is flexible
enough to be the same regardless of the type of analysis that is requested while
still conveying generic information about how the request should be processed,
in particular it should allow for a generic cache management and sampling.

```yaml
request:

  options:
    updates: None # maybe something like [None, notify, push] ?
	# this is probably not useful, would be for chaning data?
	# for streams this wont work since its not the same request, we need
	# some other type of request to handle those.

    # more service specific options can be added here.


  inputs:

    - source: spam
      offset: 0
      length: 1048576
      sample: 0.6

    - source: eggs
      offset: 0
      length: 1048576
      sample: 0.6

  reports:

    # We could have some helper function generating
    # default request profiles for this thing.

    - completion: 0.0
      precision: 2097152
      detour: false

    - completion: 0.1
      precision: 1048576
      detour: true

    - completion: 0.5
      precision: 65536
      detour: false

    - completion: 1.0
      precision: 4096
      detour: true

  cache:

    # this should be generated using recomendations.
    # not every client should make its own guesses.
    # but it must be allowed to.

    - blocksz: 1024
      lookup: true
      commit: false

    - blocksz: 4096
      lookup: true
      commit: true

    - blocksz: 65536
      lookup: true
      commit: false
```

This format can easily be extended to support multi-dimensional inputs by simply
having offsets, lengths, sample rates and blocksizes being arrays.
