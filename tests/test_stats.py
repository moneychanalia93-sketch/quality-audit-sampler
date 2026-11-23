import unittest

from sampler.stats import MIN_AUDITS, flag_text, sample_size, sentence, wilson_interval


# Tests for the maths alone. The expected numbers were worked out by hand.
class WilsonTests(unittest.TestCase):
    # By hand: p = 0.9, z^2 = 3.8416, shrink = 1.038416,
    # centre = (0.9 + 0.019208) / 1.038416 = 0.88520,
    # half = 1.96 * sqrt(0.0009 + 0.00009604) / 1.038416 = 0.05957.
    def test_ninety_of_one_hundred(self):
        low, high = wilson_interval(90, 100)
        self.assertAlmostEqual(low, 0.8256, places=4)
        self.assertAlmostEqual(high, 0.9448, places=4)

    # With 0 passes in 10 the low end is exactly 0 and the high end is 0.2775.
    # With 10 of 10 we still do not claim 100% for sure: the low end is 0.7225.
    # With no audits at all we know nothing: 0 to 1.
    def test_edge_cases(self):
        low, high = wilson_interval(0, 10)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.2775, places=4)
        low, high = wilson_interval(10, 10)
        self.assertAlmostEqual(low, 0.7225, places=4)
        self.assertEqual(high, 1.0)
        self.assertEqual(wilson_interval(0, 0), (0.0, 1.0))

    def test_interval_always_holds_the_observed_rate_and_stays_in_0_to_1(self):
        for total in (1, 5, 30, 200):
            for passes in range(total + 1):
                low, high = wilson_interval(passes, total)
                self.assertLessEqual(0.0, low)
                self.assertLessEqual(high, 1.0)
                self.assertLessEqual(low, passes / total + 1e-9)
                self.assertGreaterEqual(high, passes / total - 1e-9)

    def test_more_audits_give_a_narrower_interval(self):
        small = wilson_interval(9, 10)
        big = wilson_interval(900, 1000)
        self.assertLess(big[1] - big[0], small[1] - small[0])


class SampleSizeTests(unittest.TestCase):
    # By hand: 1.96^2 * 0.5 * 0.5 / 0.05^2 = 3.8416 * 0.25 / 0.0025 = 384.16, so 385.
    # And 3.8416 * 0.25 / 0.0009 = 1067.1, so 1068.
    def test_half_guess_needs_385_for_five_points_and_1068_for_three(self):
        self.assertEqual(sample_size(0.05), 385)
        self.assertEqual(sample_size(0.03), 1068)

    # By hand: 3.8416 * 0.05 * 0.95 / 0.0004 = 456.19, rounded up to 457.
    def test_a_lower_guessed_rate_needs_fewer_audits(self):
        self.assertEqual(sample_size(0.02, p=0.05), 457)
        self.assertLess(sample_size(0.02, p=0.05), sample_size(0.02))

    def test_a_bad_margin_or_rate_guess_is_refused(self):
        for margin in (0, 1, -0.1, 5):
            with self.assertRaises(ValueError):
                sample_size(margin)
        with self.assertRaises(ValueError):
            sample_size(0.05, p=1.5)


class TextTests(unittest.TestCase):
    def test_sentences_use_the_interval(self):
        self.assertEqual(sentence(90, 100),
                         "We are 95% sure the true pass rate is between 82.6% and 94.5%.")
        self.assertEqual(sentence(90, 100, "error"),
                         "We are 95% sure the true error rate is between 5.5% and 17.4%.")

    def test_flags_for_low_good_and_no_audits(self):
        self.assertEqual(flag_text(90, 100, 0.95), "BELOW TARGET")
        self.assertEqual(flag_text(98, 100, 0.95), "ok")
        self.assertEqual(flag_text(0, 0, 0.95), "no audits yet")

    def test_small_sample_gets_a_warning(self):
        self.assertLess(10, MIN_AUDITS)
        self.assertIn("too few to say", flag_text(8, 10, 0.95))
        self.assertIn("BELOW TARGET", flag_text(8, 10, 0.95))
        self.assertNotIn("too few", flag_text(98, 100, 0.95))
