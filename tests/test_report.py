import unittest

from sampler import db
from sampler.report import build_report
from tests.helpers import DbTestCase


# Tests for the report. We write audits straight into the database with known counts.
class ReportTests(DbTestCase):
    # Audit the first `total` items of a workflow: `fails` of them fail.
    def audit_workflow(self, workflow, total, fails, source="random"):
        ids = [item["id"] for item in self.items if item["workflow"] == workflow][:total]
        rows = [(item_id, "fail" if n < fails else "pass", "other" if n < fails else "")
                for n, item_id in enumerate(ids)]
        db.add_audits(self.conn, rows, source)

    def report_text(self, target=0.95):
        return "\n".join(build_report(self.conn, target))

    def test_no_audits_gives_a_helpful_message(self):
        self.assertIn("No audits recorded yet", self.report_text())

    def test_overall_rates_and_sentence(self):
        self.audit_workflow("address_check", 100, 10)
        text = self.report_text()
        self.assertIn("pass rate 90.0% (90 of 100), error rate 10.0%", text)
        self.assertIn("We are 95% sure the true pass rate is between 82.6% and 94.5%.", text)
        self.assertIn("We are 95% sure the true error rate is between 5.5% and 17.4%.", text)

    def test_a_low_workflow_is_flagged_and_a_good_one_is_not(self):
        self.audit_workflow("address_check", 100, 10)
        self.audit_workflow("data_entry", 100, 1)
        lines = {line.split()[0]: line for line in self.report_text().splitlines()
                 if line.startswith("  ") and line.split()}
        self.assertIn("BELOW TARGET", lines["address_check"])
        self.assertTrue(lines["data_entry"].rstrip().endswith("ok"))
        self.assertEqual(db.overall_counts(self.conn), (200, 189))

    def test_a_small_sample_gets_the_warning(self):
        self.audit_workflow("address_check", 12, 1)
        self.assertIn("only 12 audits: too few to say", self.report_text())

    def test_focus_audits_are_not_counted_in_the_rates(self):
        self.audit_workflow("address_check", 50, 0)
        self.audit_workflow("data_entry", 30, 30, source="focus")
        text = self.report_text()
        self.assertIn("pass rate 100.0% (50 of 50)", text)
        self.assertIn("focus audits not counted here: 30", text)
        self.assertNotIn("data_entry", text)
