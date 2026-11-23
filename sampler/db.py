"""All the SQL: two tables, `items` (the work) and `audits` (the results)."""

import sqlite3

# `truly_bad` is the hidden truth used only by the simulation and the
# pretend auditor. `source` says how the audit was drawn: "random" or "focus".
SCHEMA = """
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    workflow TEXT NOT NULL,
    worker TEXT NOT NULL,
    day INTEGER NOT NULL,
    truly_bad INTEGER NOT NULL
);
CREATE TABLE audits (
    item_id INTEGER PRIMARY KEY REFERENCES items(id),
    result TEXT NOT NULL CHECK (result IN ('pass', 'fail')),
    reason TEXT NOT NULL,
    source TEXT NOT NULL
);
"""


# Open the database file (it is created if missing). Rows act like dicts.
def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Throw away any old tables and make empty new ones. Seeding starts over.
def reset(conn):
    conn.executescript("DROP TABLE IF EXISTS audits; DROP TABLE IF EXISTS items;" + SCHEMA)


# Save a list of item dicts. The :name placeholders keep values out of the SQL text.
def add_items(conn, items):
    with conn:
        conn.executemany(
            "INSERT INTO items VALUES (:id, :workflow, :worker, :day, :truly_bad)", items)


# Load items as plain dicts, sorted by id. By default only items nobody has
# audited yet, so one item is never audited twice.
def load_items(conn, only_unaudited=True):
    sql = "SELECT * FROM items"
    if only_unaudited:
        sql += " WHERE id NOT IN (SELECT item_id FROM audits)"
    return [dict(row) for row in conn.execute(sql + " ORDER BY id")]


# Every item id, and every id that already has an audit. Used to check a results file.
def known_and_audited_ids(conn):
    known = {row[0] for row in conn.execute("SELECT id FROM items")}
    audited = {row[0] for row in conn.execute("SELECT item_id FROM audits")}
    return known, audited


# Save audit rows: a list of (item_id, result, reason). All or nothing.
def add_audits(conn, rows, source):
    with conn:
        conn.executemany("INSERT INTO audits VALUES (?, ?, ?, ?)",
                         [(item_id, result, reason, source) for item_id, result, reason in rows])


# Workers with at least one failed audit on an item from the last
# `recent_days` days of data. These are the workers "focus" mode looks at.
def focus_workers(conn, recent_days):
    rows = conn.execute(
        "SELECT DISTINCT items.worker FROM audits JOIN items ON items.id = audits.item_id"
        " WHERE audits.result = 'fail'"
        " AND items.day > (SELECT MAX(day) FROM items) - ? ORDER BY items.worker",
        (recent_days,))
    return {row[0] for row in rows}


# (audits, passes) over all audits drawn at random. Focus audits are left
# out: they look at suspect workers on purpose, so they would make us look worse.
def overall_counts(conn):
    row = conn.execute("SELECT COUNT(*), SUM(result = 'pass') FROM audits"
                       " WHERE source != 'focus'").fetchone()
    return row[0], row[1] or 0


# How many focus audits exist (they are counted separately, not in the rates).
def focus_audit_count(conn):
    return conn.execute("SELECT COUNT(*) FROM audits WHERE source = 'focus'").fetchone()[0]


# (name, audits, passes) for each workflow or each worker.
# `column` is only ever "workflow" or "worker" (checked below), never user text.
def group_counts(conn, column):
    if column not in ("workflow", "worker"):
        raise ValueError("column must be workflow or worker")
    sql = (f"SELECT items.{column}, COUNT(*), SUM(audits.result = 'pass')"
           " FROM audits JOIN items ON items.id = audits.item_id"
           f" WHERE audits.source != 'focus' GROUP BY items.{column} ORDER BY items.{column}")
    return [(name, total, passes) for name, total, passes in conn.execute(sql)]


# How many items exist in total.
def item_count(conn):
    return conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
