import re


def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return s or 'untitled'

# revised 2026-08-23

# revised 2026-08-31
