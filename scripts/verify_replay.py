#!/usr/bin/env python3
"""Compare deterministic aggregate output with the frozen public aggregate JSON."""
import argparse, hashlib
from pathlib import Path
EXPECTED='2020eafd809b3a6888fefa35c48ad036322f3c4faaab0056303168791b60f7e1'
def verify(generated,committed):
    a=Path(generated).read_bytes();b=Path(committed).read_bytes()
    assert a==b,'REPLAY MISMATCH: generated JSON differs from committed aggregate'
    h=hashlib.sha256(b).hexdigest()
    assert h==EXPECTED,f'AGGREGATE SHA256 MISMATCH: {h}'
    return h
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('generated');p.add_argument('committed')
    a=p.parse_args()
    print('PASS deterministic aggregate bytes and SHA-256',verify(a.generated,a.committed))
