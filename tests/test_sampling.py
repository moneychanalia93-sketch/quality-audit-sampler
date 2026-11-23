import random
import unittest

from sampler import db
from sampler.sampling import allocate, focus_sample, simple_sample, stratified_sample
from sampler.seed import WORKFLOWS, make_items
from tests.helpers import DbTestCase, make_item


# Tests for the three ways of picking items. Items are plain dicts, no database needed.
class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.items = make_items(2000, seed=42)

    def test_simple_sample_has_the_asked_size_and_never_repeats_an_item(self):
        picked = simple_sample(self.items, 1000, random.Random(1))
        ids = [item["id"] for item in picked]
        self.assertEqual(len(ids), 1000)
        self.assertEqual(len(set(ids)), 1000)

    def test_a_seed_repeats_the_draw_whatever_the_input_order(self):
        first = simple_sample(self.items, 100, random.Random(5))
        self.assertEqual(first, simple_sample(self.items, 100, random.Random(5)))
        self.assertEqual(first, simple_sample(list(reversed(self.items)), 100, random.Random(5)))
        self.assertNotEqual(first, simple_sample(self.items, 100, random.Random(6)))

    def test_too_big_or_zero_sample_is_refused(self):
        for size in (2001, 0):
            with self.assertRaises(ValueError):
                simple_sample(self.items, size, random.Random(1))

    def test_stratified_sample_has_the_asked_size_and_no_repeats(self):
        picked = stratified_sample(self.items, 333, random.Random(1))
        ids = [item["id"] for item in picked]
        self.assertEqual(len(ids), 333)
        self.assertEqual(len(set(ids)), 333)

    def test_stratified_gives_each_workflow_its_share(self):
        picked = stratified_sample(self.items, 200, random.Random(1))
        for name in WORKFLOWS:
            size = sum(item["workflow"] == name for item in self.items)
            got = sum(item["workflow"] == name for item in picked)
            self.assertAlmostEqual(got, 200 * size / 2000, delta=1)


# Tests for splitting n between groups.
class AllocateTests(unittest.TestCase):
    def test_shares_are_proportional_and_leftovers_go_to_the_biggest_fractions(self):
        self.assertEqual(allocate({"a": 50, "b": 30, "c": 20}, 10), {"a": 5, "b": 3, "c": 2})
        # Shares: a 3.5, b 2.1, c 0.4 -> floors 3, 2, 0 -> one place left; a has the biggest fraction (.5).
        self.assertEqual(allocate({"a": 35, "b": 21, "c": 4}, 6), {"a": 4, "b": 2, "c": 0})

    def test_quotas_add_up_to_n_and_never_exceed_the_group(self):
        counts = {"a": 801, "b": 499, "c": 301, "d": 241, "e": 158}
        for n in (1, 7, 50, 99, 333, 1000, 2000):
            quota = allocate(counts, n)
            self.assertEqual(sum(quota.values()), n, n)
            self.assertTrue(all(quota[name] <= counts[name] for name in counts))


# Tests for focus mode (it needs the database to find workers with recent failures).
class FocusTests(DbTestCase):
    def audit(self, item_id, result):
        reason = "other" if result == "fail" else ""
        db.add_audits(self.conn, [(item_id, result, reason)], "random")

    def first_item(self, worker, day):
        return next(i for i in self.items if i["worker"] == worker and i["day"] == day)

    def test_focus_workers_are_those_with_a_recent_failure(self):
        self.audit(self.first_item("W05", 10)["id"], "fail")      # recent fail: counts
        self.audit(self.first_item("W06", 9)["id"], "fail")       # recent fail: counts
        self.audit(self.first_item("W07", 2)["id"], "fail")       # old fail: ignored
        self.audit(self.first_item("W08", 10)["id"], "pass")      # recent pass: ignored
        self.assertEqual(db.focus_workers(self.conn, 3), {"W05", "W06"})

    def test_focus_sample_only_picks_the_focus_workers(self):
        picked = focus_sample(self.items, 40, random.Random(1), {"W05", "W06"})
        self.assertEqual(len(picked), 40)
        self.assertTrue(all(item["worker"] in {"W05", "W06"} for item in picked))

    def test_focus_sample_returns_everything_when_the_pool_is_small(self):
        pool = [make_item(i, worker="W01") for i in range(1, 6)] + [make_item(9, worker="W02")]
        picked = focus_sample(pool, 50, random.Random(1), {"W01"})
        self.assertEqual(sorted(item["id"] for item in picked), [1, 2, 3, 4, 5])

    def test_audited_items_are_not_offered_again(self):
        self.audit(1, "pass")
        offered = {item["id"] for item in db.load_items(self.conn)}
        self.assertNotIn(1, offered)
        self.assertEqual(len(offered), 1999)
