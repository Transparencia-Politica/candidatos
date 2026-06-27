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
    from score_candidate import CAMARA, fetch_json
except ModuleNotFoundError:  # pragma: no cover - import shim
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, help="topic slug, e.g. tributacao-da-riqueza")
    parser.add_argument("--descriptors", required=True, help="comma-separated TECAD descriptors")
    parser.add_argument("--years", default="2023,2024,2025", help="comma-separated years")
    args = parser.parse_args(argv)

    descriptors = [d.strip() for d in args.descriptors.split(",") if d.strip()]
    years = [int(y) for y in args.years.split(",") if y.strip()]
    laws = discover(args.topic, descriptors, years)
    json.dump({"laws": laws}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
