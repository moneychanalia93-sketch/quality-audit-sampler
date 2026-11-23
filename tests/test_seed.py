import unittest

from sampler import db
from sampler.seed import HIGH_ERROR_WORKERS, WORKERS, WORKFLOWS, make_items
from tests.helpers import DbTestCase


# Tests for the fake data.
class SeedTests(unittest.TestCase):
    def test_same_seed_gives_same_items_and_a_different_seed_does_not(self):
        self.assertEqual(make_items(500, seed=1), make_items(500, seed=1))
        self.assertNotEqual(make_items(500, seed=1), make_items(500, seed=2))

    def test_shape_of_the_data(self):
        items = make_items(2000)
        self.assertEqual([item["id"] for item in items], list(range(1, 2001)))
        self.assertEqual({item["workflow"] for item in items}, set(WORKFLOWS))
        self.assertEqual({item["worker"] for item in items}, set(WORKERS))
        self.assertEqual({item["day"] for item in items}, set(range(1, 11)))
        self.assertEqual((len(WORKFLOWS), len(WORKERS)), (5, 20))

    def test_error_rates_are_a_few_percent_and_higher_for_the_risky_workers(self):
        items = make_items(20000)
        risky = [item["truly_bad"] for item in items if item["worker"] in HIGH_ERROR_WORKERS]
        others = [item["truly_bad"] for item in items if item["worker"] not in HIGH_ERROR_WORKERS]
        self.assertGreater(sum(risky) / len(risky), 2 * sum(others) / len(others))
        overall = sum(item["truly_bad"] for item in items) / len(items)
        self.assertTrue(0.02 < overall < 0.07, overall)


# Tests for saving the fake data in the database.
class SeedDatabaseTests(DbTestCase):
    def test_items_are_saved_and_seeding_again_starts_over(self):
        self.assertEqual(db.item_count(self.conn), 2000)
        db.reset(self.conn)
        db.add_items(self.conn, make_items(50))
        self.assertEqual(db.item_count(self.conn), 50)
