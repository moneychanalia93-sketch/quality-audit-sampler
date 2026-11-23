"""Three ways to pick items. Each takes a random generator, so a seed repeats the draw."""


# Make sure we are asking for a sensible number of items.
def check_size(items, n):
    if n < 1:
        raise ValueError("the sample size must be at least 1")
    if n > len(items):
        raise ValueError(f"cannot pick {n} items: only {len(items)} are available")


# Simple random sample: every item has the same chance.
# rng.sample never picks the same item twice. We sort first so the
# result depends on the seed only, not on the order the items came in.
def simple_sample(items, n, rng):
    check_size(items, n)
    return rng.sample(sorted(items, key=lambda item: item["id"]), n)


# Split n between groups in proportion to group size, using whole numbers
# that add up to exactly n. Each group gets the rounded-down share first.
# The few leftover places go to the groups with the biggest cut-off fractions.
def allocate(counts, n):
    total = sum(counts.values())
    shares = {name: n * count / total for name, count in counts.items()}
    quota = {name: int(share) for name, share in shares.items()}
    leftover = n - sum(quota.values())
    by_fraction = sorted(shares, key=lambda name: (-(shares[name] - quota[name]), name))
    for name in by_fraction[:leftover]:
        quota[name] += 1
    return quota


# Stratified sample: every workflow gets its fair share of the draw,
# then we pick at random inside each workflow. Small workflows are
# never missed by bad luck.
def stratified_sample(items, n, rng):
    check_size(items, n)
    groups = {}
    for item in sorted(items, key=lambda item: item["id"]):
        groups.setdefault(item["workflow"], []).append(item)
    quota = allocate({name: len(group) for name, group in groups.items()}, n)
    picked = []
    for name in sorted(groups):
        picked += rng.sample(groups[name], quota[name])
    return picked


# Focus sample: pick only from the given workers (the ones with recent failures).
# If they have fewer than n items left, we return all of them.
# This is NOT a fair sample of everyone. Do not use it for the overall rate.
def focus_sample(items, n, rng, workers):
    if n < 1:
        raise ValueError("the sample size must be at least 1")
    pool = [item for item in sorted(items, key=lambda item: item["id"])
            if item["worker"] in workers]
    return rng.sample(pool, min(n, len(pool)))
