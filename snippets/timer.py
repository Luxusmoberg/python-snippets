import time
from contextlib import contextmanager


@contextmanager
def timer(label='block'):
    t = time.perf_counter()
    yield
    print(f'{label}: {time.perf_counter() - t:.3f}s')
