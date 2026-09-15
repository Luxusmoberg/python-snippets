def flatten(xs):
    out = []
    for x in xs:
        out.extend(x if isinstance(x, list) else [x])
    return out

# revised 2026-08-22

# revised 2026-08-30

# revised 2026-09-07

# revised 2026-09-15
