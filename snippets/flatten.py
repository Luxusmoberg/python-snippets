def flatten(xs):
    out = []
    for x in xs:
        out.extend(x if isinstance(x, list) else [x])
    return out
