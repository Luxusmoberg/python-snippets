import time


def retry(fn, n=3, delay=0.5):
    for i in range(n):
        try:
            return fn()
        except Exception:
            if i == n - 1:
                raise
            time.sleep(delay * (2 ** i))

# revised 2026-08-24

# revised 2026-09-01
