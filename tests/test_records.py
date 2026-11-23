import csv
import unittest

from sampler import db
from sampler.records import check_row, pretend_audit, read_results, write_sample
from tests.helpers import DbTestCase

KNOWN = {1, 2, 3, 4, 5}


# Tests for checking one result row.
class CheckRowTests(unittest.TestCase):
    def test_good_rows_are_accepted_in_any_letter_case(self):
        self.assertIsNone(check_row({"item_id": "1", "result": "pass", "reason": ""}, KNOWN, set()))
        row = {"item_id": "2", "result": "FAIL", "reason": "Wrong_Value"}
        self.assertIsNone(check_row(row, KNOWN, set()))

    def test_item_id_must_be_a_whole_number(self):
        self.assertIn("whole number", check_row({"item_id": "abc", "result": "pass"}, KNOWN, set()))
        self.assertIn("whole number", check_row({"item_id": "", "result": "pass"}, KNOWN, set()))

    def test_unknown_and_already_audited_items_are_refused(self):
        self.assertEqual(check_row({"item_id": "99", "result": "pass"}, KNOWN, set()),
                         "unknown item")
        self.assertEqual(check_row({"item_id": "1", "result": "pass"}, KNOWN, {1}),
                         "item already audited")

    def test_result_must_be_pass_or_fail(self):
        self.assertIn("pass or fail", check_row({"item_id": "1", "result": "maybe"}, KNOWN, set()))

    def test_a_fail_needs_a_known_reason_and_a_pass_must_not_have_one(self):
        for reason in ("", "dunno"):
            row = {"item_id": "1", "result": "fail", "reason": reason}
            self.assertIn("reason", check_row(row, KNOWN, set()))
        row = {"item_id": "1", "result": "pass", "reason": "other"}
        self.assertIn("must not", check_row(row, KNOWN, set()))


# Tests for reading and writing the CSV files.
class FileTests(DbTestCase):
    def test_bad_rows_are_counted_and_good_rows_kept(self):
        path = self.write_file("r.csv", "item_id,result,reason\n"
                               "1,pass,\n2,fail,other\n3,maybe,\n4,fail,\n99,pass,\n1,pass,\n")
        good, problems = read_results(path, {1, 2, 3, 4}, set())
        self.assertEqual(good, [(1, "pass", ""), (2, "fail", "other")])
        self.assertEqual([line for line, _ in problems], [4, 5, 6, 7])

    def test_a_hidden_excel_marker_at_the_start_of_the_file_is_ignored(self):
        path = self.write_file("r.csv", "\ufeffitem_id,result,reason\n1,pass,\n")
        good, problems = read_results(path, KNOWN, set())
        self.assertEqual((good, problems), ([(1, "pass", "")], []))

    def test_a_file_without_the_needed_columns_is_refused(self):
        path = self.write_file("r.csv", "id,outcome\n1,pass\n")
        with self.assertRaises(ValueError):
            read_results(path, KNOWN, set())

    def test_write_sample_leaves_result_and_reason_empty(self):
        path = self.path("s.csv")
        write_sample(path, self.items[:3])
        with open(path, newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual([row["item_id"] for row in rows], ["1", "2", "3"])
        self.assertEqual({row["result"] for row in rows}, {""})

    def test_pretend_audit_follows_the_hidden_truth(self):
        sample = self.path("s.csv")
        write_sample(sample, self.items[:200])
        truth = {item["id"]: item["truly_bad"] for item in self.items}
        pretend_audit(sample, self.path("r.csv"), truth, seed=1)
        known, audited = db.known_and_audited_ids(self.conn)
        good, problems = read_results(self.path("r.csv"), known, audited)
        self.assertEqual(problems, [])
        fails = {item_id for item_id, result, _ in good if result == "fail"}
        self.assertEqual(fails, {i for i in range(1, 201) if truth[i]})
