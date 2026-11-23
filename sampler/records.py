"""Reading and writing the CSV files: the sample out, the audit results in."""

import csv
import random

REASONS = ["wrong_value", "missing_field", "wrong_category", "late_entry", "other"]
SAMPLE_COLUMNS = ["item_id", "workflow", "worker", "day", "result", "reason"]


# Write the picked items to a CSV. `result` and `reason` are left empty
# for the auditor to fill in. (Extra keys such as id and truly_bad are not written.)
def write_sample(path, items):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, SAMPLE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow({**item, "item_id": item["id"]})


# Check one result row. Returns a short problem text, or None if the row is fine.
# `seen_ids` holds items that already have an audit, so nothing is counted twice.
def check_row(row, known_ids, seen_ids):
    text = (row.get("item_id") or "").strip()
    if not text.isdigit():
        return "item_id is not a whole number"
    if int(text) not in known_ids:
        return "unknown item"
    if int(text) in seen_ids:
        return "item already audited"
    result = (row.get("result") or "").strip().lower()
    reason = (row.get("reason") or "").strip().lower()
    if result not in ("pass", "fail"):
        return "result must be pass or fail"
    if result == "fail" and reason not in REASONS:
        return "a fail needs a reason code: " + ", ".join(REASONS)
    if result == "pass" and reason:
        return "a pass must not have a reason"
    return None


# Read a results CSV. Returns (good_rows, problems).
# good_rows are (item_id, result, reason). problems are (line_number, text).
# A bad row is counted and skipped; it does not stop the other rows.
def read_results(path, known_ids, audited_ids):
    good, problems = [], []
    seen = set(audited_ids)
    # utf-8-sig: Excel can put a hidden marker at the start of a CSV; this skips it.
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not {"item_id", "result"} <= set(reader.fieldnames or []):
            raise ValueError("the CSV needs the columns item_id, result and reason")
        for line, row in enumerate(reader, start=2):  # line 1 is the header
            problem = check_row(row, known_ids, seen)
            if problem:
                problems.append((line, problem))
                continue
            seen.add(int(row["item_id"]))
            good.append((int(row["item_id"]), row["result"].strip().lower(),
                         (row.get("reason") or "").strip().lower()))
    return good, problems


# Pretend to be the auditor, for demos and tests. Reads a sample CSV and
# fills in result and reason from the hidden truth (`truth` maps id -> truly_bad).
def pretend_audit(sample_path, out_path, truth, seed):
    rng = random.Random(seed)
    with open(sample_path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        failed = truth[int(row["item_id"])]
        row["result"] = "fail" if failed else "pass"
        row["reason"] = rng.choice(REASONS) if failed else ""
    with open(out_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, SAMPLE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
