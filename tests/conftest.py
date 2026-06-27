"""Shared pytest fixtures. Tests run against the dockerized MySQL (docker compose up -d).

The DB is shared and seeded (real topics/laws/keywords/politics/scores live in it). A test
must never leak rows into it — a stray law would then be baked into `data/*.json` and the public
`docs/data/scorecards.json`. So the `conn` fixture snapshots the seeded row ids before each test
and deletes anything inserted during it, restoring the seeded baseline on teardown.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import db  # noqa: E402

# Cache tables: fully rebuildable from the Câmara API, so wipe them wholesale around each test.
_CACHE_TABLES = ["votes", "roll_calls"]
# Seeded tables: keep the baseline rows, delete only what a test inserts. Child-first (FK) order.
_SEEDED_TABLES = ["scores", "keywords", "laws", "topics", "politics"]


def _safe(conn, sql, params=None):
    try:
        conn.execute(sql, params) if params is not None else conn.execute(sql)
        conn.commit()
    except Exception:
        pass  # table may not exist yet (pre-implementation)


def _ids(conn, table):
    try:
        return {r["id"] for r in conn.execute(f"SELECT id FROM {table}").fetchall()}
    except Exception:
        return set()


def _delete_inserted(conn, table, keep_ids):
    """Delete rows whose id is not in the pre-test baseline (i.e. inserted by the test)."""
    if keep_ids:
        placeholders = ",".join(["?"] * len(keep_ids))
        _safe(conn, f"DELETE FROM {table} WHERE id NOT IN ({placeholders})", tuple(keep_ids))
    else:
        _safe(conn, f"DELETE FROM {table}")


@pytest.fixture
def conn():
    c = db.init_db()
    for table in _CACHE_TABLES:
        _safe(c, f"DELETE FROM {table}")
    baseline = {table: _ids(c, table) for table in _SEEDED_TABLES}
    yield c
    for table in _CACHE_TABLES:
        _safe(c, f"DELETE FROM {table}")
    for table in _SEEDED_TABLES:  # child-first, so FK constraints stay satisfied
        _delete_inserted(c, table, baseline[table])
    c.close()


def law_id(conn, slug):
    return conn.execute("SELECT id FROM laws WHERE slug = ?", (slug,)).fetchone()["id"]
