"""Shared test setup: a temporary folder with a freshly seeded database."""

import contextlib
import io
import os
import tempfile
import unittest

from sampler import db
from sampler.cli import main
from sampler.seed import make_items


# Base class for tests that need a database file and a place for CSV files.
# Every test gets its own temporary folder, deleted afterwards.
class DbTestCase(unittest.TestCase):
    # Make the folder and a database holding 2,000 fake items.
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.db_path = self.path("test.db")
        self.items = make_items(2000, seed=42)
        self.conn = db.connect(self.db_path)
        db.reset(self.conn)
        db.add_items(self.conn, self.items)

    # Close the database, then delete the folder (Windows needs the file closed).
    def tearDown(self):
        self.conn.close()
        self.folder.cleanup()

    # Full path of a file inside the temporary folder.
    def path(self, name):
        return os.path.join(self.folder.name, name)

    # Write text to a file in the folder and return its path.
    def write_file(self, name, text):
        path = self.path(name)
        with open(path, "w", newline="", encoding="utf-8") as file:
            file.write(text)
        return path

    # Run a command line (without the program name) and return what it printed.
    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(list(args))
        return output.getvalue()


# A tiny item for tests that do not need the database.
def make_item(item_id, workflow="a", worker="W01", day=1):
    return {"id": item_id, "workflow": workflow, "worker": worker, "day": day, "truly_bad": 0}
