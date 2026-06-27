"""Shared pytest fixtures. Tests run against the dockerized MySQL (docker compose up -d)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import db  # noqa: E402


def _safe(conn, sql):
    try:
        conn.execute(sql)
        conn.commit()
    except Exception:
        pass  # table may not exist yet (pre-implementation)


@pytest.fixture
def conn():
    c = db.init_db()
    # isolate the cache tables (defensive: they may not exist before implementation)
    _safe(c, "DELETE FROM votos")
    _safe(c, "DELETE FROM votacoes")
    yield c
    _safe(c, "DELETE FROM votos")
    _safe(c, "DELETE FROM votacoes")
    c.close()


def law_id(conn, slug):
    return conn.execute("SELECT id FROM laws WHERE slug = ?", (slug,)).fetchone()["id"]
