import unittest

from sampler import db
from tests.helpers import DbTestCase


# Tests that run the real commands, the way a person would.
class CliTests(DbTestCase):
    def db_args(self):
        return ["--db", self.db_path]

    def test_seed_writes_items(self):
        out = self.run_cli("seed", "--db", self.path("new.db"), "--items", "300")
        self.assertIn("Wrote 300 fake items", out)

    def test_a_missing_database_gives_a_clear_message(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("report", "--db", self.path("nothing.db"))
        self.assertIn("seed", str(caught.exception))

    def test_same_seed_writes_the_same_file(self):
        for name in ("a.csv", "b.csv"):
            self.run_cli("sample", "--n", "60", "--mode", "stratified", "--seed", "9",
                         "--out", self.path(name), *self.db_args())
        with open(self.path("a.csv"), encoding="utf-8") as a, \
                open(self.path("b.csv"), encoding="utf-8") as b:
            self.assertEqual(a.read(), b.read())

    def test_sample_bigger_than_the_data_is_a_clear_error(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("sample", "--n", "5000", "--out", self.path("s.csv"), *self.db_args())
        self.assertIn("only 2000", str(caught.exception))

    def test_focus_mode_without_any_failures_is_a_clear_error(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("sample", "--n", "20", "--mode", "focus", "--out", self.path("s.csv"),
                         *self.db_args())
        self.assertIn("failed audit", str(caught.exception))

    def test_a_whole_audit_cycle(self):
        self.run_cli("sample", "--n", "300", "--mode", "stratified", "--out", self.path("s.csv"),
                     *self.db_args())
        self.run_cli("pretend-audit", self.path("s.csv"), "--out", self.path("r.csv"),
                     *self.db_args())
        out = self.run_cli("record", self.path("r.csv"), *self.db_args())
        self.assertIn("Recorded 300 audits. Rejected 0 bad rows.", out)
        report = self.run_cli("report", *self.db_args())
        self.assertIn("Audited 300 of 2000 items", report)
        self.assertIn("We are 95% sure the true pass rate is between", report)
        again = self.run_cli("record", self.path("r.csv"), *self.db_args())
        self.assertIn("Recorded 0 audits. Rejected 300 bad rows.", again)

    def test_record_prints_the_bad_rows(self):
        path = self.write_file("r.csv", "item_id,result,reason\n1,pass,\n2,oops,\n3,fail,\n")
        out = self.run_cli("record", path, *self.db_args())
        self.assertIn("Recorded 1 audits. Rejected 2 bad rows.", out)
        self.assertIn("line 3: result must be pass or fail", out)

    def test_focus_mode_after_a_recent_failure(self):
        item = next(i for i in self.items if i["day"] == 10)
        db.add_audits(self.conn, [(item["id"], "fail", "other")], "random")
        out = self.run_cli("sample", "--n", "20", "--mode", "focus", "--out", self.path("f.csv"),
                           *self.db_args())
        self.assertIn(f"Focus workers: {item['worker']}", out)

    def test_sample_size_prints_the_formula_and_the_answer(self):
        out = self.run_cli("sample-size", "--margin", "0.05")
        self.assertIn("n = z^2 * p * (1 - p) / margin^2", out)
        self.assertIn("384.16, rounded UP to 385", out)
        with self.assertRaises(SystemExit):
            self.run_cli("sample-size", "--margin", "2")
