"""The maths: Wilson interval, sample size, plain sentences, flags."""

import math

Z = 1.96          # the z-number for 95% confidence
MIN_AUDITS = 30   # with fewer audits than this, a rate is too shaky to trust


# The Wilson interval: a low and a high number that the true pass rate
# probably sits between. Better than the simple formula when the sample is
# small or the rate is near 0% or 100%. With no audits we know nothing: 0 to 1.
def wilson_interval(passes, total, z=Z):
    if total == 0:
        return 0.0, 1.0
    p = passes / total
    z2 = z * z
    shrink = 1 + z2 / total
    centre = (p + z2 / (2 * total)) / shrink
    half = z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / shrink
    return max(0.0, centre - half), min(1.0, centre + half)


# How many audits are needed so the result is within +/- `margin` of the
# truth (95% of the time). p is our guess of the rate; 0.5 is the safest
# guess because it needs the most audits. We always round UP.
def sample_size(margin, p=0.5, z=Z):
    if not 0 < margin < 1:
        raise ValueError("margin must be between 0 and 1 (for example 0.05)")
    if not 0 <= p <= 1:
        raise ValueError("p must be between 0 and 1")
    return math.ceil(round(z * z * p * (1 - p) / (margin * margin), 6))


# The plain-words sentence we print under a rate.
def sentence(passes, total, what="pass"):
    low, high = wilson_interval(passes, total)
    if what == "error":
        low, high = 1 - high, 1 - low
    return f"We are 95% sure the true {what} rate is between {low:.1%} and {high:.1%}."


# The flag shown next to a workflow or worker.
# A low rate is flagged. A small sample gets a warning, because with few
# audits one or two failures can move the rate a lot.
def flag_text(passes, total, target):
    if total == 0:
        return "no audits yet"
    text = "BELOW TARGET" if passes / total < target else "ok"
    if total < MIN_AUDITS:
        text += " (only %d audits: too few to say)" % total
    return text
