"""Canonical identity for complete measured rows; scheduling order is not data."""
def canonical_measured(samples):
    indexed={}
    for sample in samples:
        key=tuple(sample[k] for k in ("mode","shard","dataset","seq"))
        if key in indexed:
            raise ValueError("duplicate measured sample identity")
        indexed[key]=sample
    return [indexed[key] for key in sorted(indexed)]

def require_same_measured(left,right):
    if canonical_measured(left)!=canonical_measured(right):
        raise ValueError("aggregate measured sample values/identities drift")
