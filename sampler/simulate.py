"""Check the method: does the 95% interval really hold the truth about 95% of the time?"""

from sampler.sampling import simple_sample, stratified_sample
from sampler.stats import wilson_interval

METHODS = {"simple": simple_sample, "stratified": stratified_sample}


# The real pass rate of the whole fake population. We can know it
# only because we made the data ourselves.
def true_pass_rate(items):
    return 1 - sum(item["truly_bad"] for item in items) / len(items)


# Draw `runs` samples of size n. For each one, audit it perfectly (we
# know the truth), build the 95% interval, and check if it holds the true rate.
# Returns (share of intervals that held the truth, average interval width).
def run_method(items, n, runs, method, rng):
    truth = true_pass_rate(items)
    held = 0
    width = 0.0
    for _ in range(runs):
        picked = METHODS[method](items, n, rng)
        passes = sum(1 - item["truly_bad"] for item in picked)
        low, high = wilson_interval(passes, n)
        held += low <= truth <= high
        width += high - low
    return held / runs, width / runs


# Run every method at a small and a larger sample size, and print a table.
def run_simulation(items, runs, rng, sizes=(30, 200)):
    lines = [
        f"Fake population: {len(items)} items, true pass rate {true_pass_rate(items):.2%} "
        "(known, because we made the data).",
        f"Each row repeats the draw {runs} times and counts how often the "
        "95% interval held the true rate.",
        "",
        f"  {'method':<12}{'audits':>7}{'held the truth':>17}{'avg width':>12}",
    ]
    for method in METHODS:
        for n in sizes:
            held, width = run_method(items, n, runs, method, rng)
            lines.append(f"  {method:<12}{n:>7}{held:>17.1%}{width:>12.1%}")
    return lines
