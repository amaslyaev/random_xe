# -*- coding: utf-8 -*-
#
# 2018 Alexander Maslyaev <maslyaev@gmail.com>
#
# No copyright. No license. It's up to you what to do with this text.
# http://creativecommons.org/publicdomain/zero/1.0/

""" Random number generator with eXtra Entropy.

Features:
1. CompoundRandom class implements combining several random number sources
   into one full featured generator.
2. HashRandom class implements pseudo-random number generator which is
   surprisingly has sense in cryptographic applications. Of course in
   addition to SystemRandom.
"""

from random import Random, SystemRandom, BPF as _BPF, RECIP_BPF as _RECIP_BPF
from functools import reduce as _reduce
from operator import xor as _xor
from hashlib import sha256 as _sha256

class CompoundRandom(SystemRandom):
    def __new__(cls, *sources):
        """Create an instance.
        Positional arguments must be descendants of Random"""
        if not all(isinstance(src, Random) for src in sources):
            raise TypeError("all the sources must be descendants of Random")
        return super().__new__(cls)
    
    def __init__(self, *sources):
        """Initialize an instance.
        Positional arguments must be descendants of Random"""
        self.sources = sources
        super().__init__()
        
    def getrandbits(self, k):
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        return _reduce(_xor, (src.getrandbits(k) for src in self.sources), 0)
    
    def random(self):
        """Get the next random number in the range [0.0, 1.0)."""
        return self.getrandbits(_BPF) * _RECIP_BPF

class HashRandom(SystemRandom):
    def __new__(cls, entropy, hashobj=_sha256):
        """Create an instance."""
        return super().__new__(cls)
    
    def __init__(self, entropy, hashtype=_sha256):
        """Initialize an instance.
        entropy - some initializing data (bytes, string, list or whatever)
        hashobj - any class that inplements update(v) and digest() functions,
          and digest_size attribute. By default: hashlib.sha256"""
        def _to_bytes(val):
            return val if isinstance(val, bytes) or isinstance(val, bytearray) \
                   else (bytes(val, 'utf-8') if isinstance(val, str) \
                   else _to_bytes(str(val)))
        entropy_bytes = _to_bytes(entropy)
        self._hidden_hash = hashtype()
        self._prod_hash = hashtype()
        self._digest_bits = self._prod_hash.digest_size * 8
        if not self._digest_bits:
            raise TypeError("specified hashtype cannot be used (digest_size=0)")
        self._hidden_hash.update(entropy_bytes)
        self._prod_hash.update(self._hidden_hash.digest() + entropy_bytes)
        self._curr_int = int.from_bytes(self._prod_hash.digest(), 'big')
        self._remain_bits = self._digest_bits
        super().__init__()
        
    def getrandbits(self, k):
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        if k < 0:
            raise ValueError("requested number of bits must not be negative")
        ans = 0
        while k:
            if not self._remain_bits:
                self._hidden_hash.update(self._hidden_hash.digest())
                self._prod_hash.update(self._prod_hash.digest() +
                                       self._hidden_hash.digest())
                self._curr_int = int.from_bytes(self._prod_hash.digest(), 'big')
                self._remain_bits = self._digest_bits
            bits2use = min(k, self._remain_bits)
            self._remain_bits -= bits2use
            k -= bits2use
            ans = (ans << bits2use) | (self._curr_int & ((1 << bits2use) - 1))
            self._curr_int = self._curr_int >> bits2use
        return ans
    
    def random(self):
        """Get the next random number in the range [0.0, 1.0)."""
        return self.getrandbits(_BPF) * _RECIP_BPF

if __name__ == "__main__":
    from hashlib import sha3_224
    tst = CompoundRandom(HashRandom('Hello'), HashRandom('world', sha3_224))
    print('Selftest...')
    assert hex(tst.getrandbits(256)) == \
           '0xf7bd21d15f08c14b69475985ba7edbef2979665c9030d6d9d6cddf7a9228587'
    assert hex(tst.getrandbits(256)) == \
           '0xf7ecbd5fb8429c3552b6d76f4ccb00268aa73909006a230e6a4e624423d927b0'
    print('...passed')
