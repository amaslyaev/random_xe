from random import Random, SystemRandom
from random import BPF as _BPF, RECIP_BPF as _RECIP_BPF
from functools import reduce as _reduce
from operator import xor as _xor
from hashlib import sha256 as _sha256

class CompoundRandom(SystemRandom):
    def __new__(cls, *sources):
        """Creates an instance."""
        if not all(isinstance(src, Random) for src in sources):
            raise TypeError("all the sources must be descendants of Random")
        return super().__new__(cls)
    
    def __init__(self, *sources):
        """Initialize an instance."""
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
        """Initialize an instance."""
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
        #return _reduce(lambda acc, val: acc^val,
        #               (src.getrandbits(k) for src in self.sources), 0)
    
    def random(self):
        """Get the next random number in the range [0.0, 1.0)."""
        return self.getrandbits(_BPF) * _RECIP_BPF

##hr1 = HashRandom('123')
##with open('tst123.bin', 'wb') as f:
##	hr123 = HashRandom('123')
##	for i in range(1024*10):
##		wtn = f.write(hr123.getrandbits(1024*8).to_bytes(1024, 'big'))
