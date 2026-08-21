def chunk(xs, n):
    return [xs[i:i + n] for i in range(0, len(xs), n)]

# revised 2026-08-21
