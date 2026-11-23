"""Make fake work items. Everything here is invented."""

import random

# Five fake workflows and how common each one is (bigger = more items).
WORKFLOWS = {"address_check": 40, "invoice_match": 25, "photo_label": 15,
             "data_entry": 12, "refund_review": 8}
WORKERS = [f"W{number:02d}" for number in range(1, 21)]
DAYS = 10

# Most workers make a mistake on 3.5% of items. Three workers make one
# on 9%. The audit does not know this. The report should find it.
HIGH_ERROR_WORKERS = {"W03", "W11", "W17"}
NORMAL_ERROR = 0.035
HIGH_ERROR = 0.09


# Build `count` fake items. The same seed always gives the same items.
# `truly_bad` is the hidden truth (1 = the work has an error). A real tool
# would not know it. We keep it so we can check the method against the truth.
def make_items(count, seed=42):
    rng = random.Random(seed)
    names = list(WORKFLOWS)
    weights = list(WORKFLOWS.values())
    items = []
    for item_id in range(1, count + 1):
        worker = rng.choice(WORKERS)
        error_rate = HIGH_ERROR if worker in HIGH_ERROR_WORKERS else NORMAL_ERROR
        items.append({
            "id": item_id,
            "workflow": rng.choices(names, weights)[0],
            "worker": worker,
            "day": rng.randint(1, DAYS),
            "truly_bad": 1 if rng.random() < error_rate else 0,
        })
    return items
