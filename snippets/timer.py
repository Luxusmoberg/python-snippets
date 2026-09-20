import time
from contextlib import contextmanager


@contextmanager
def timer(label='block'):
    t = time.perf_counter()
    yield
    print(f'{label}: {time.perf_counter() - t:.3f}s')

# revised 2026-08-27

# revised 2026-09-04

# revised 2026-09-12

# revised 2026-09-20
