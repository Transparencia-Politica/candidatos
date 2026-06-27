#!/usr/bin/env python3
"""Persist the topic/law config and scored-candidate results to versioned JSON.

The database is not in git, so the curated law set, the discovered laws, and the
candidate scorecards live only in MySQL. This tool exports them to `data/` so they
can be committed and restored on a fresh DB.

It writes three files (see DATA_DIR):
  - laws.json        config: topics + every law + its keywords (the full law set).
  - candidates.json  config: the roster of scored candidates (camara_id + identity).
  - snapshot.json    baked result: the above PLUS politics + computed scores.

Scores are keyed by stable identifiers (camara_id, keyword slug) — never the DB's
auto-increment ids — so a load rebuilds the same results even if ids differ.

Usage:
  python app/snapshot.py export                 # DB  -> data/*.json
  python app/snapshot.py load                   # snapshot.json -> DB (config + results)
  python app/snapshot.py load --config-only     # laws + candidates only (re-score yourself)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    import db
except ModuleNotFoundError:  # pragma: no cover - import shim
    from app import db

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SITE_DATA_DIR = os.path.join(ROOT_DIR, "docs", "data")


def _topics(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT slug, title, description, cod_temas, sort_order FROM topics ORDER BY sort_order, slug"
    ).fetchall()
    return [
        {
            "slug": r["slug"],
            "title": r["title"],
            "description": r["description"],
            "cod_temas": db.from_json(r.get("cod_temas"), []),
            "sort_order": r["sort_order"],
        }
        for r in rows
    ]


def _laws(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT l.slug, l.camara_proposicao_id, l.label, l.kind, l.number, l.year,
               l.description, l.source_url, l.is_key, l.wealth_relevant, l.sort_order,
               t.slug AS topic_slug, l.id AS law_id
        FROM laws l JOIN topics t ON t.id = l.topic_id
        ORDER BY t.sort_order, l.sort_order, l.slug
        """
    ).fetchall()
    out = []
    for r in rows:
        kws = conn.execute(
            "SELECT slug, label, description, direction, weight, wealth_relevant, sort_order "
            "FROM keywords WHERE law_id = ? ORDER BY sort_order, slug",
            (r["law_id"],),
        ).fetchall()
        out.append(
            {
                "topic_slug": r["topic_slug"],
                "slug": r["slug"],
                "camara_proposicao_id": r["camara_proposicao_id"],
                "label": r["label"],
                "kind": r["kind"],
                "number": r["number"],
                "year": r["year"],
                "description": r["description"],
                "source_url": r["source_url"],
                "is_key": int(r["is_key"]),
                "wealth_relevant": int(r["wealth_relevant"]),
                "sort_order": r["sort_order"],
                "keywords": [
                    {
                        "slug": k["slug"],
                        "label": k["label"],
                        "description": k["description"],
                        "direction": k["direction"],
                        "weight": k["weight"],
                        "wealth_relevant": int(k["wealth_relevant"]),
                        "sort_order": k["sort_order"],
                    }
                    for k in kws
                ],
            }
        )
    return out


def _politics(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT camara_id, tse_sq, tse_year, tse_uf, tse_election_id, name, party, uf,
               birth_date, occupation, profile_json, wealth_total, wealth_capital,
               wealth_buckets_json
        FROM politics ORDER BY camara_id
        """
    ).fetchall()
    return [
        {
            "camara_id": r["camara_id"],
            "tse_sq": r["tse_sq"],
            "tse_year": r["tse_year"],
            "tse_uf": r["tse_uf"],
            "tse_election_id": r["tse_election_id"],
            "name": r["name"],
            "party": r["party"],
            "uf": r["uf"],
            "birth_date": r["birth_date"],
            "occupation": r["occupation"],
            "profile": db.from_json(r.get("profile_json"), {}),
            "wealth_total": r["wealth_total"],
            "wealth_capital": r["wealth_capital"],
            "wealth_buckets": db.from_json(r.get("wealth_buckets_json"), {}),
        }
        for r in rows
    ]


def _candidates(politics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The roster (config) — just enough to re-score each candidate from scratch."""
    return [
        {k: p[k] for k in ("camara_id", "name", "party", "uf", "tse_sq", "tse_year", "tse_uf", "tse_election_id")}
        for p in politics
    ]


def _scores(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT p.camara_id, k.slug AS keyword_slug, s.score_value, s.self_interest_value,
               s.vote_status, s.vote_label, s.stance, s.present_count, s.nominal_count,
               s.coverage_value, s.evidence_json
        FROM scores s
        JOIN politics p ON p.id = s.politic_id
        JOIN keywords k ON k.id = s.keyword_id
        ORDER BY p.camara_id, k.slug
        """
    ).fetchall()
    return [
        {
            "camara_id": r["camara_id"],
            "keyword_slug": r["keyword_slug"],
            "score_value": r["score_value"],
            "self_interest_value": r["self_interest_value"],
            "vote_status": r["vote_status"],
            "vote_label": r["vote_label"],
            "stance": r["stance"],
            "present_count": r["present_count"],
            "nominal_count": r["nominal_count"],
            "coverage_value": r["coverage_value"],
            "evidence": db.from_json(r.get("evidence_json"), {}),
        }
        for r in rows
    ]


def export_snapshot(conn) -> dict[str, Any]:
    topics = _topics(conn)
    laws = _laws(conn)
    politics = _politics(conn)
    return {
        "topics": topics,
        "laws": laws,
        "candidates": _candidates(politics),
        "politics": politics,
        "scores": _scores(conn),
    }


def _write(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_files(snapshot: dict[str, Any], data_dir: str = DATA_DIR) -> list[str]:
    os.makedirs(data_dir, exist_ok=True)
    laws_file = os.path.join(data_dir, "laws.json")
    cands_file = os.path.join(data_dir, "candidates.json")
    snap_file = os.path.join(data_dir, "snapshot.json")
    _write(laws_file, {"topics": snapshot["topics"], "laws": snapshot["laws"]})
    _write(cands_file, {"candidates": snapshot["candidates"]})
    _write(snap_file, snapshot)
    return [laws_file, cands_file, snap_file]


def export_site(conn, site_data_dir: str = SITE_DATA_DIR) -> str:
    """Bake the assembled scorecards for every candidate to a static JSON file.

    Writes the exact `{generated_at, scorecards: [...]}` shape the frontend renders,
    so the GitHub Pages page can read it with no backend. Source of truth is the live
    DB (same as `export`) via db.get_scorecards.
    """
    payload = db.get_scorecards(conn, None)
    os.makedirs(site_data_dir, exist_ok=True)
    out_file = os.path.join(site_data_dir, "scorecards.json")
    _write(out_file, payload)
    return out_file


def load_config(conn, data: dict[str, Any]) -> None:
    """Restore topics + laws + keywords (the law set) — no results."""
    for t in data["topics"]:
        conn.execute(
            """
            INSERT INTO topics (slug, title, description, cod_temas, sort_order, updated_at)
            VALUES (:slug, :title, :description, :cod_temas, :sort_order, :updated_at)
            ON DUPLICATE KEY UPDATE
              title = VALUES(title), description = VALUES(description),
              cod_temas = VALUES(cod_temas), sort_order = VALUES(sort_order),
              updated_at = VALUES(updated_at)
            """,
            {
                "slug": t["slug"],
                "title": t["title"],
                "description": t["description"],
                "cod_temas": db.as_json(t.get("cod_temas", [])),
                "sort_order": t.get("sort_order", 0),
                "updated_at": db.now_iso(),
            },
        )
    topic_ids = {r["slug"]: r["id"] for r in conn.execute("SELECT id, slug FROM topics").fetchall()}
    for law in data["laws"]:
        db.upsert_law(
            conn,
            topic_id=topic_ids[law["topic_slug"]],
            slug=law["slug"],
            camara_proposicao_id=law["camara_proposicao_id"],
            label=law["label"],
            kind=law["kind"],
            number=str(law["number"]),
            year=law["year"],
            description=law["description"],
            source_url=law["source_url"],
            is_key=law.get("is_key", 0),
            wealth_relevant=law.get("wealth_relevant", 1),
            sort_order=law.get("sort_order", 0),
        )
        law_id = conn.execute("SELECT id FROM laws WHERE slug = ?", (law["slug"],)).fetchone()["id"]
        for kw in law.get("keywords", []):
            db.upsert_keyword(
                conn,
                law_id=law_id,
                slug=kw["slug"],
                label=kw["label"],
                description=kw["description"],
                direction=kw["direction"],
                weight=kw["weight"],
                wealth_relevant=kw.get("wealth_relevant", 1),
                sort_order=kw.get("sort_order", 0),
            )
    conn.commit()


def load_results(conn, data: dict[str, Any]) -> None:
    """Restore politics + scores (the baked scorecards). Assumes config already loaded."""
    for p in data.get("politics", []):
        db.upsert_politic(
            conn,
            camara_id=p["camara_id"],
            tse_sq=p["tse_sq"],
            tse_year=p["tse_year"],
            tse_uf=p["tse_uf"],
            tse_election_id=p["tse_election_id"],
            name=p["name"],
            party=p["party"],
            uf=p["uf"],
            birth_date=p.get("birth_date"),
            occupation=p.get("occupation", ""),
            profile=p.get("profile", {}),
            wealth_total=p["wealth_total"],
            wealth_capital=p["wealth_capital"],
            wealth_buckets=p.get("wealth_buckets", {}),
        )
    politic_ids = {r["camara_id"]: r["id"] for r in conn.execute("SELECT id, camara_id FROM politics").fetchall()}
    keyword_ids = {r["slug"]: r["id"] for r in conn.execute("SELECT id, slug FROM keywords").fetchall()}
    skipped = 0
    for s in data.get("scores", []):
        pid = politic_ids.get(s["camara_id"])
        kid = keyword_ids.get(s["keyword_slug"])
        if pid is None or kid is None:
            skipped += 1
            continue
        db.upsert_score(
            conn,
            politic_id=pid,
            keyword_id=kid,
            score_value=s["score_value"],
            self_interest_value=s["self_interest_value"],
            vote_status=s["vote_status"],
            vote_label=s["vote_label"],
            stance=s["stance"],
            present_count=s["present_count"],
            nominal_count=s["nominal_count"],
            coverage_value=s["coverage_value"],
            evidence=s.get("evidence", {}),
        )
    conn.commit()
    if skipped:
        print(f"warning: skipped {skipped} score(s) with no matching candidate/keyword", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["export", "load", "site"])
    parser.add_argument("--db", default=None, help="Database URL; defaults to DATABASE_URL")
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--site-data-dir", default=SITE_DATA_DIR, help="site: where to write scorecards.json")
    parser.add_argument("--config-only", action="store_true", help="load: laws + candidates only, skip baked results")
    args = parser.parse_args(argv)

    if args.command == "site":
        conn = db.connect(args.db)
        try:
            payload = db.get_scorecards(conn, None)
            out_file = export_site(conn, args.site_data_dir)
        finally:
            conn.close()
        print(f"Baked {len(payload['scorecards'])} scorecard(s) -> {out_file}")
        return 0

    if args.command == "export":
        conn = db.connect(args.db)
        try:
            snapshot = export_snapshot(conn)
        finally:
            conn.close()
        files = write_files(snapshot, args.data_dir)
        print(
            f"Exported {len(snapshot['laws'])} laws, {len(snapshot['candidates'])} candidates, "
            f"{len(snapshot['scores'])} scores ->"
        )
        for f in files:
            print(f"  {f}")
        return 0

    # load
    with open(os.path.join(args.data_dir, "snapshot.json"), encoding="utf-8") as f:
        data = json.load(f)
    conn = db.init_db(args.db)  # ensure schema exists
    try:
        load_config(conn, data)
        if not args.config_only:
            load_results(conn, data)
    finally:
        conn.close()
    what = "config (laws + keywords)" if args.config_only else "config + results (politics + scores)"
    print(f"Loaded {what} from {args.data_dir}/snapshot.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
