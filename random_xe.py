# -*- coding: utf-8 -*-
#
# 2018 Alexander Maslyaev <maslyaev@gmail.com>
#
# No copyright. No license. It's up to you what to do with this text.
# http://creativecommons.org/publicdomain/zero/1.0/

""" Random number generator with eXtra Enthropy.

Features:
1. CompoundRandom class implements combining several random number sources
   into one full featured generator.
2. HashRandom class implements pseudo-random number generator which is
   surprisingly has sense in cryptographic applications.
"""

from random import Random, SystemRandom
from random import BPF as _BPF, RECIP_BPF as _RECIP_BPF
from functools import reduce as _reduce
from operator import xor as _xor
from hashlib import sha256 as _sha256

class CompoundRandom(SystemRandom):
    def __new__(cls, *sources):
        """Creates an instance.
        
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
    def __new__(cls, enthropy, hashobj=_sha256):
        """Creates an instance."""
        return super().__new__(cls)
    
    def __init__(self, enthropy, hashtype=_sha256):
        """Initialize an instance.
        
        entropy - some initializing data (bytes, string, list or whatever)
        hashobj - any class that inplements update(v) and digest() functions,
          and digest_size attribute. By default: hashlib.sha256"""
        def _to_bytes(val):
            return val if isinstance(val, bytes) or isinstance(val, bytearray) \
                   else (bytes(val, 'utf-8') if isinstance(val, str) \
                   else _to_bytes(str(val)))
        enthropy_bytes = _to_bytes(enthropy)
        self._hidden_hash = hashtype()
        self._prod_hash = hashtype()
        self._digest_bits = self._prod_hash.digest_size * 8
        self._hidden_hash.update(enthropy_bytes)
        self._prod_hash.update(enthropy_bytes + self._hidden_hash.digest())
        self._curr_int = int.from_bytes(self._prod_hash.digest(), 'big')
        self._remain_bits = self._digest_bits
        super().__init__()
        
    def getrandbits(self, k):
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        bits2use = min(k, self._remain_bits)
        self._remain_bits -= bits2use
        k -= bits2use
        ans = self._curr_int & ((1 << bits2use) - 1)
        self._curr_int = self._curr_int >> bits2use
        while k:
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
