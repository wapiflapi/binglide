
This documentation for the next binglide version is targeted for technical users
or people with an interest in the design decisions that are being made. Most of
the documents will discuss design and implementation, some might be about the
APIs.

# Architecture

The first version of binglide has shown that there is a need for somewhat
complex cache systems and that having multiple threads computing at the same
time would result in a faster user experience. This are some of the goals:

  - Code as much stuff as posisble in Python.
  - Being able to switch to C or other technologies when needed.
  - Be scalable, main target is a PC but clusters should be possible.

Separating the code in two parts, a backend doing analysis and frontend
presenteing the results has obvious advantages.


## Frontend

### Python/QT/Vispy

This would be the natural follow up after binglide v1. Vispy is curently being
developed and promisses fun stuff with OpenGL and QT integration.

### Web UI

I don't know much about this but it should be considered. Aldo Cortesi is
working on something like this with [binvis](binvis.io). If that is stable and
extensible we might want to plug into that.


## Backend

The backend should allow workers to compute what they should be computing and at
the same time offer APIs for those workers to delagate work to others. The two
main topics that need to be tackled are:

  - [Multiprocess control, delegation](./multiprocessing.md)
  - [Cache management](./cache.md)

