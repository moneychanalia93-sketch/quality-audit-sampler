import random
import unittest

from sampler.seed import make_items
from sampler.simulate import run_method


# Tests for the simulation. We use 300 repeats here to keep the tests quick.
class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.items = make_items(2000, seed=42)

    def test_the_95_percent_interval_holds_the_truth_about_95_percent_of_the_time(self):
        for method in ("simple", "stratified"):
            held, _ = run_method(self.items, 200, 300, method, random.Random(1))
            self.assertTrue(0.92 <= held <= 0.99, f"{method}: {held}")

    def test_a_bigger_sample_gives_a_narrower_interval(self):
        _, small = run_method(self.items, 30, 50, "simple", random.Random(1))
        _, big = run_method(self.items, 200, 50, "simple", random.Random(1))
        self.assertLess(big, small)

    def test_same_seed_gives_the_same_numbers(self):
        first = run_method(self.items, 100, 40, "simple", random.Random(4))
        second = run_method(self.items, 100, 40, "simple", random.Random(4))
        self.assertEqual(first, second)
