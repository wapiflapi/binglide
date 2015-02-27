
```yaml
# TODO:
# inputs, lengths and precisions should be vectors in order to handle
# multi-dimensional data properly. This shouldnt pose any problems.

request:

  options:
    # service specific.

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

