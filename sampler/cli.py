"""The command line: python -m sampler <command>"""

import argparse
import os
import random
import sys
from contextlib import closing

from sampler import db, records
from sampler.report import build_report
from sampler.sampling import focus_sample, simple_sample, stratified_sample
from sampler.seed import make_items
from sampler.simulate import run_simulation
from sampler.stats import Z, sample_size


# Open a database that must already exist. If it does not, stop with a clear message.
def open_db(path):
    if not os.path.exists(path):
        sys.exit(f"error: {path} not found. Run `python -m sampler seed` first.")
    return db.connect(path)


# seed: write fake items (starting over if the database already exists).
def cmd_seed(args):
    items = make_items(args.items, args.seed)
    with closing(db.connect(args.db)) as conn:
        db.reset(conn)
        db.add_items(conn, items)
    bad = sum(item["truly_bad"] for item in items)
    print(f"Wrote {len(items)} fake items to {args.db} (seed {args.seed}).")
    print(f"Hidden truth, used only by `simulate` and `pretend-audit`: "
          f"{bad} items have an error ({bad / len(items):.1%}).")


# sample: draw N items that nobody has audited yet and write them to a CSV.
def cmd_sample(args):
    rng = random.Random(args.seed)
    with closing(open_db(args.db)) as conn:
        items = db.load_items(conn)
        if args.mode == "simple":
            picked = simple_sample(items, args.n, rng)
        elif args.mode == "stratified":
            picked = stratified_sample(items, args.n, rng)
        else:
            workers = db.focus_workers(conn, args.recent_days)
            if not workers:
                sys.exit(f"error: no worker has a failed audit in the last "
                         f"{args.recent_days} days. Record some audits first.")
            picked = focus_sample(items, args.n, rng, workers)
            print("Focus workers:", ", ".join(sorted(workers)))
    records.write_sample(args.out, picked)
    print(f"Picked {len(picked)} items (mode {args.mode}, seed {args.seed}) -> {args.out}")
    for name in sorted({item["workflow"] for item in picked}):
        print(f"  {name:<15}{sum(item['workflow'] == name for item in picked):>5}")


# pretend-audit: fill in a sample CSV using the hidden truth (demo only).
def cmd_pretend_audit(args):
    with closing(open_db(args.db)) as conn:
        truth = {item["id"]: item["truly_bad"] for item in db.load_items(conn, False)}
    count = records.pretend_audit(args.sample_file, args.out, truth, args.seed)
    print(f"Pretend auditor filled in {count} rows -> {args.out}")


# record: load audit results from a CSV. Bad rows are counted and skipped.
def cmd_record(args):
    with closing(open_db(args.db)) as conn:
        known, audited = db.known_and_audited_ids(conn)
        good, problems = records.read_results(args.results_file, known, audited)
        db.add_audits(conn, good, "focus" if args.focus else "random")
    print(f"Recorded {len(good)} audits. Rejected {len(problems)} bad rows.")
    for line, text in problems[:5]:
        print(f"  line {line}: {text}")
    if len(problems) > 5:
        print(f"  ... and {len(problems) - 5} more")


# report: print pass and error rates with their intervals.
def cmd_report(args):
    with closing(open_db(args.db)) as conn:
        print("\n".join(build_report(conn, args.target)))


# sample-size: how many audits for a chosen margin of error, with the working shown.
def cmd_sample_size(args):
    n = sample_size(args.margin, args.p)
    exact = Z * Z * args.p * (1 - args.p) / (args.margin ** 2)
    print(f"Audits needed for a margin of error of {args.margin * 100:g} percentage points "
          "(95% confidence)")
    print()
    print("Formula:  n = z^2 * p * (1 - p) / margin^2")
    print(f"Where:    z = {Z} (95%), p = {args.p} (our guess of the rate; 0.5 is the safest),")
    print(f"          margin = {args.margin}")
    print(f"Worked:   n = {Z}^2 * {args.p} * (1 - {args.p}) / {args.margin}^2")
    print(f"            = {Z * Z:.4f} * {args.p * (1 - args.p):.4f} / {args.margin ** 2:.6f}")
    print(f"            = {exact:.2f}, rounded UP to {n} audits")


# simulate: repeat the sampling many times on fake data with a known truth.
def cmd_simulate(args):
    items = make_items(args.items, args.data_seed)
    print("\n".join(run_simulation(items, args.runs, random.Random(args.seed))))


# Describe every command and its options.
def build_parser():
    parser = argparse.ArgumentParser(prog="sampler", description="Quality audit sampler")
    commands = parser.add_subparsers(dest="command", required=True)

    def add(name, func, help_text, with_db=True):
        sub = commands.add_parser(name, help=help_text)
        sub.set_defaults(func=func)
        if with_db:
            sub.add_argument("--db", default="audit.db")
        return sub

    sub = add("seed", cmd_seed, "write fake work items")
    sub.add_argument("--items", type=int, default=2000)
    sub.add_argument("--seed", type=int, default=42)

    sub = add("sample", cmd_sample, "pick items to audit")
    sub.add_argument("--n", type=int, required=True)
    sub.add_argument("--mode", choices=["simple", "stratified", "focus"], default="simple")
    sub.add_argument("--seed", type=int, default=1)
    sub.add_argument("--recent-days", type=int, default=3)
    sub.add_argument("--out", default="sample.csv")

    sub = add("pretend-audit", cmd_pretend_audit, "fill a sample CSV from the hidden truth")
    sub.add_argument("sample_file")
    sub.add_argument("--out", default="results.csv")
    sub.add_argument("--seed", type=int, default=7)

    sub = add("record", cmd_record, "load audit results from a CSV")
    sub.add_argument("results_file")
    sub.add_argument("--focus", action="store_true", help="these audits came from a focus draw")

    sub = add("report", cmd_report, "pass and error rates with intervals")
    sub.add_argument("--target", type=float, default=0.95)

    sub = add("sample-size", cmd_sample_size, "how many audits are enough", with_db=False)
    sub.add_argument("--margin", type=float, default=0.05)
    sub.add_argument("--p", type=float, default=0.5)

    sub = add("simulate", cmd_simulate, "check the interval on fake data", with_db=False)
    sub.add_argument("--runs", type=int, default=1000)
    sub.add_argument("--seed", type=int, default=1)
    sub.add_argument("--items", type=int, default=2000)
    sub.add_argument("--data-seed", type=int, default=42)
    return parser


# Read the command line and run the chosen command. A bad value
# (for example a sample bigger than the data) becomes a clear message, not a crash.
def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, KeyError, OSError) as error:
        sys.exit(f"error: {error}")
