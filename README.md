## Random number generator with eXtra Entropy.

This little module is a simple and reliable way to improve randomness of any random or pseudo-random number generator.

We never being 100% sure in real randomness and cryptographic quality of any externally-provided RNG, and this is a good idea to be able to add some addition entropy to by own hands. This module provides following features:
1. Easy way to combine unrestricted number of randomness sources (CompoundRandom class).
2. Tool to transform several additional bytes of extra entropy into complete random-like mess (HashRandom class).

### Why we can be sure that combining independent random sources can only improve quality of RNG
*coming soon...*

### How to embed

There are two ways to embed this functionality into your project:
1. Get this module by `pip install random_xe` and then import into your module by `import random_xe`.
2. Directly download [random_xe.py](/random_xe.py) file and adopt it into your project.

### How to use

Import this module:
```python
>>> import random_xe
```
Create and try HashRandom PRNG initialized with 'Hello world':
```python
>>> import random_xe
>>> myrandom1 = random_xe.HashRandom('Hello world')
>>> myrandom1.randint(100, 200)
156
>>> myrandom1.gauss(20, 10)
8.243867125227318
```
myrandom1 uses SHA-256 hashing function (option by default).

Let`s try to combine this PRNG with another HashRandom based on SHA3-512 and initialized from user input:
```python
>>> from hashlib import sha3_512
>>> myrandom2 = random_xe.CompoundRandom(myrandom1, random_xe.HashRandom(input('Type somethig: '), sha3_512))
Type somethig: ldjggndjKfuT830
>>> myrandom2.getrandbits(128)
171962833922528548054430533031273437533
```

It is very good idea ALWAYS combine additional entropy with SystemRandom source:
```python
>>> from getpass import getpass
>>> from time import perf_counter
>>> # Three sources:
>>> # - SystemRandom;
>>> # - user input;
>>> # - timing.
>>> def super_myrandom():
    t_start = perf_counter()
    return random_xe.CompoundRandom(random_xe.SystemRandom(),
        random_xe.HashRandom(
            getpass('Type somethig:'), sha3_512),
        random_xe.HashRandom(perf_counter() - t_start))

>>> myrandom3 = super_myrandom()
>>> myrandom3.getrandbits(128)
214560115455406687033892278367232976155
```
