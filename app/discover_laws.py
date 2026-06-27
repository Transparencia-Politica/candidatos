#!/usr/bin/env python3
"""Topic -> law discovery (curation aid).

Given a topic's controlled-vocabulary descriptors (TECAD terms, see
research/09-topic-to-law-discovery.md), search the Câmara `keywords=` index, keep the
bills that actually went to a nominal roll-call, and emit proposed LAW seed objects in
the same shape as db.py's seed lists. A human curates them (sets direction, is_key,
wealth_relevant, keywords) before loading — this tool proposes, it does not auto-publish.

External Câmara API paths (/proposicoes, /votacoes) and JSON fields (siglaTipo, ementa…)
stay in Portuguese — they are the upstream contract.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from typing import Any, Callable

try:
    import db
    from score_candidate import CAMARA, fetch_json
except ModuleNotFoundError:  # pragma: no cover - import shim
    from app import db
    from app.score_candidate import CAMARA, fetch_json

VOTABLE_TYPES = {"PL", "PEC", "PLP", "MPV"}


def search_by_descriptors(
    descriptors: list[str],
    years: list[int],
    *,
    fetch: Callable[[str], dict[str, Any]] = fetch_json,
    itens: int = 30,
) -> list[dict[str, Any]]:
    """Union of votable proposições found by querying each descriptor across each year."""
    found: dict[Any, dict[str, Any]] = {}
    for descriptor in descriptors:
        for year in years:
            query = urllib.parse.urlencode(
                {"keywords": descriptor, "ano": year, "itens": itens, "ordem": "DESC", "ordenarPor": "id"}
            )
            for p in fetch(f"{CAMARA}/proposicoes?{query}").get("dados", []):
                if p.get("siglaTipo") in VOTABLE_TYPES:
                    found.setdefault(p["id"], p)
    return list(found.values())


def has_nominal_roll_call(proposicao_id: Any, *, fetch: Callable[[str], dict[str, Any]] = fetch_json) -> bool:
    roll_calls = fetch(f"{CAMARA}/proposicoes/{proposicao_id}/votacoes").get("dados", [])
    return any("Sim:" in (rc.get("descricao") or "") for rc in roll_calls)


def filter_voted(
    proposicoes: list[dict[str, Any]],
    *,
    fetch: Callable[[str], dict[str, Any]] = fetch_json,
) -> list[dict[str, Any]]:
    return [p for p in proposicoes if has_nominal_roll_call(p["id"], fetch=fetch)]


def to_seed_law(topic_slug: str, p: dict[str, Any], *, is_key: int = 0) -> dict[str, Any]:
    """Map a proposição to a curatable LAW seed object (db.py LAWS format)."""
    kind = p.get("siglaTipo", "")
    return {
        "topic_slug": topic_slug,
        "slug": f"{kind.lower()}-{p.get('numero')}-{p.get('ano')}",
        "camara_proposicao_id": p["id"],
        "label": f"{kind} {p.get('numero')}/{p.get('ano')}",
        "kind": kind,
        "number": str(p.get("numero")),
        "year": p.get("ano"),
        "description": (p.get("ementa") or "")[:255],
        "source_url": p.get("uri") or f"{CAMARA}/proposicoes/{p['id']}",
        "is_key": is_key,
        "wealth_relevant": 1,  # curator confirms
        "sort_order": 0,
    }


def discover(
    topic_slug: str,
    descriptors: list[str],
    years: list[int],
    *,
    fetch: Callable[[str], dict[str, Any]] = fetch_json,
) -> list[dict[str, Any]]:
    """descriptors -> votable proposições -> keep voted -> proposed LAW seed objects."""
    proposicoes = search_by_descriptors(descriptors, years, fetch=fetch)
    voted = filter_voted(proposicoes, fetch=fetch)
    return [to_seed_law(topic_slug, p) for p in voted]


def search_by_themes(
    cod_temas: list[int],
    years: list[int],
    *,
    fetch: Callable[[str], dict[str, Any]] = fetch_json,
    itens: int = 100,
) -> list[dict[str, Any]]:
    """Union of votable proposições in the given Câmara theme(s) (codTema), per year.

    The simple by-theme workflow (research/01): a topic maps to one or more codTema
    (e.g. wealth/finance -> 70 Finanças, 40 Economia), and laws are the bills in it.
    """
    found: dict[Any, dict[str, Any]] = {}
    for cod_tema in cod_temas:
        for year in years:
            query = urllib.parse.urlencode(
                {"codTema": cod_tema, "ano": year, "itens": itens, "ordem": "DESC", "ordenarPor": "id"}
            )
            for p in fetch(f"{CAMARA}/proposicoes?{query}").get("dados", []):
                if p.get("siglaTipo") in VOTABLE_TYPES:
                    found.setdefault(p["id"], p)
    return list(found.values())


def discover_by_theme(
    topic_slug: str,
    cod_temas: list[int],
    years: list[int],
    *,
    fetch: Callable[[str], dict[str, Any]] = fetch_json,
) -> list[dict[str, Any]]:
    """codTema(s) -> votable proposições -> keep voted -> proposed LAW seed objects."""
    proposicoes = search_by_themes(cod_temas, years, fetch=fetch)
    voted = filter_voted(proposicoes, fetch=fetch)
    return [to_seed_law(topic_slug, p) for p in voted]


def build_topic(conn, topic_slug: str, years: list[int], *, fetch: Callable[[str], dict[str, Any]] = fetch_json) -> dict[str, Any]:
    """Read a topic's cod_temas config -> discover voted laws -> store them under the topic.

    Append-only: laws already stored are left untouched (db.upsert_law is a no-op on hit).
    Each stored law gets one default keyword (direction +1) so it scores/renders; a curator
    can refine direction later. Roll-call ingestion (ingest.ingest_all) is a separate step.
    """
    topic = db.get_topic(conn, topic_slug)
    if topic is None:
        raise ValueError(f"unknown topic: {topic_slug}")
    laws = discover_by_theme(topic_slug, topic["cod_temas"], years, fetch=fetch)
    stored = 0
    for i, law in enumerate(laws):
        db.upsert_law(
            conn, topic_id=topic["id"], slug=law["slug"], camara_proposicao_id=law["camara_proposicao_id"],
            label=law["label"], kind=law["kind"], number=law["number"], year=law["year"],
            description=law["description"], source_url=law["source_url"],
            is_key=law["is_key"], wealth_relevant=law["wealth_relevant"], sort_order=100 + i,
        )
        law_id = conn.execute("SELECT id FROM laws WHERE slug = ?", (law["slug"],)).fetchone()["id"]
        db.upsert_keyword(
            conn, law_id=law_id, slug=law["slug"] + "-trib", label="Tributação",
            description=(law["description"] or "")[:200], direction=1, weight=1.0,
            wealth_relevant=1, sort_order=0,
        )
        stored += 1
    conn.commit()
    return {"topic": topic_slug, "cod_temas": topic["cod_temas"], "discovered": len(laws), "stored": stored}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, help="topic slug, e.g. tributacao-da-riqueza")
    parser.add_argument("--cod-temas", help="comma-separated Câmara theme codes, e.g. 70,40 (by-theme workflow)")
    parser.add_argument("--descriptors", help="comma-separated TECAD descriptors (keyword workflow)")
    parser.add_argument("--years", default="2023,2024,2025", help="comma-separated years")
    args = parser.parse_args(argv)

    years = [int(y) for y in args.years.split(",") if y.strip()]
    if args.cod_temas:
        cod_temas = [int(c) for c in args.cod_temas.split(",") if c.strip()]
        laws = discover_by_theme(args.topic, cod_temas, years)
    elif args.descriptors:
        descriptors = [d.strip() for d in args.descriptors.split(",") if d.strip()]
        laws = discover(args.topic, descriptors, years)
    else:
        parser.error("provide --cod-temas (by-theme) or --descriptors (keyword)")
    json.dump({"laws": laws}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
