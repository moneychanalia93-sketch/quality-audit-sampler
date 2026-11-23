"""Turn the recorded audits into a plain-text report."""

from sampler import db
from sampler.stats import flag_text, sentence, wilson_interval


# One table: a line per workflow (or per worker) with its pass rate,
# its 95% interval, and a flag.
def group_lines(title, rows, target):
    lines = ["", title, f"  {'name':<15}{'audits':>7}{'passed':>8}{'pass rate':>11}"
             f"   {'95% interval':<17}flag"]
    for name, total, passes in rows:
        low, high = wilson_interval(passes, total)
        lines.append(f"  {name:<15}{total:>7}{passes:>8}{passes / total:>11.1%}"
                     f"   {low:>6.1%} to {high:>6.1%}  {flag_text(passes, total, target)}")
    return lines


# Build the whole report as a list of text lines.
def build_report(conn, target):
    total, passes = db.overall_counts(conn)
    if total == 0:
        return ["No audits recorded yet. Run `sample`, audit the items, then `record`."]
    lines = [
        f"Audited {total} of {db.item_count(conn)} items "
        f"(focus audits not counted here: {db.focus_audit_count(conn)}).",
        f"Target pass rate: {target:.1%}",
        "",
        f"OVERALL: pass rate {passes / total:.1%} ({passes} of {total}), "
        f"error rate {1 - passes / total:.1%}",
        "  " + sentence(passes, total, "pass"),
        "  " + sentence(passes, total, "error"),
    ]
    lines += group_lines("BY WORKFLOW", db.group_counts(conn, "workflow"), target)
    lines += group_lines("BY WORKER", db.group_counts(conn, "worker"), target)
    return lines
