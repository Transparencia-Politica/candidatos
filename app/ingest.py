#!/usr/bin/env python3
"""Ingest a law's roll-calls into the vote cache, once.

Roll-calls are deputy-independent and immutable, so a topic's laws are fetched a
single time and stored (roll_calls/votes). Scoring then reads from the cache instead
of re-fetching per politician. See research/12-topic-packages-and-vote-caching.md.

Note: external Câmara API paths (/votacoes, /votos, /orientacoes) and API JSON field
names (tipoVoto, deputado_, orientacaoVoto) stay in Portuguese — they are the upstream
contract. Only our own code/identifiers are in English.
"""
from __future__ import annotations

import re
import time
import urllib.parse
from typing import Any, Callable

try:
    import db
    from score_candidate import CAMARA, fetch_json
except ModuleNotFoundError:  # pragma: no cover - import shim
    from app import db
    from app.score_candidate import CAMARA, fetch_json


# Some laws represent a single *destaque* (side-vote), not a bill's passage. For these,
# cache only that one roll-call so scoring reads the intended vote — keyed by proposição id
# so the pin survives a future build_topic upsert (the unique key is on proposição, not slug).
PINNED_VOTACAO = {
    2438459: "2438459-77",  # IGF destaque (Emenda de Plenário nº 8) on PLP 108/2024, 30/10/2024
}


def parse_orientation(orientations: list[dict[str, Any]], bloc_regex: str) -> str | None:
    for o in orientations:
        if re.search(bloc_regex, o.get("siglaPartidoBloco") or "", re.IGNORECASE):
            return o.get("orientacaoVoto")
    return None


def parse_roll_call(
    roll_call: dict[str, Any],
    votes: list[dict[str, Any]],
    orientations: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Pure: turn raw Câmara payloads into a roll_call record + per-deputy vote rows."""
    record = {
        "roll_call_id": str(roll_call.get("id")),
        "date": roll_call.get("data"),
        "description": roll_call.get("descricao"),
        "is_nominal": bool(votes),
        "gov_orientation": parse_orientation(orientations, "governo"),
        "opp_orientation": parse_orientation(orientations, "oposi"),
    }
    rows = [
        {"deputy_id": (r.get("deputado_") or {}).get("id"), "vote_type": r.get("tipoVoto")}
        for r in votes
        if (r.get("deputado_") or {}).get("id") is not None
    ]
    return record, rows


def ingest_law(
    conn,
    law: dict[str, Any],
    *,
    fetch: Callable[[str], dict[str, Any]] = fetch_json,
    pause: float = 0.35,
    limit_votes: int = 50,
) -> dict[str, Any]:
    """Fetch a law's roll-calls + per-deputy votes + government orientation, store in the cache.

    Only nominal roll-calls (non-empty /votos) are cached. Idempotent: re-ingesting
    upserts. `fetch` is injectable so the orchestration is testable without network.
    """
    law_id = law["id"]
    proposicao_id = law["camara_proposicao_id"]
    raw_roll_calls = fetch(
        f"{CAMARA}/proposicoes/{proposicao_id}/votacoes?ordem=DESC&ordenarPor=dataHoraRegistro"
    ).get("dados", [])

    pin = PINNED_VOTACAO.get(proposicao_id)
    if pin:
        raw_roll_calls = [rc for rc in raw_roll_calls if str(rc.get("id")) == pin]

    stored_roll_calls = 0
    stored_votes = 0
    for raw in raw_roll_calls[:limit_votes]:
        vid = urllib.parse.quote(str(raw.get("id")), safe="")
        votes = fetch(f"{CAMARA}/votacoes/{vid}/votos").get("dados", [])
        if not votes:
            continue  # symbolic vote — nothing to cache
        orientations = fetch(f"{CAMARA}/votacoes/{vid}/orientacoes").get("dados", [])
        record, vote_rows = parse_roll_call(raw, votes, orientations)
        db.upsert_roll_call(
            conn,
            roll_call_id=record["roll_call_id"],
            law_id=law_id,
            date=record["date"],
            description=record["description"],
            is_nominal=record["is_nominal"],
            gov_orientation=record["gov_orientation"],
            opp_orientation=record["opp_orientation"],
        )
        for vr in vote_rows:
            db.upsert_vote(conn, record["roll_call_id"], vr["deputy_id"], vr["vote_type"])
        stored_roll_calls += 1
        stored_votes += len(vote_rows)
        if pause:
            time.sleep(pause)

    conn.commit()
    return {"law_id": law_id, "roll_calls": stored_roll_calls, "votes": stored_votes}


def ingest_all(conn, *, pause: float = 0.35, limit_votes: int = 50, log: Callable | None = None) -> list[dict[str, Any]]:
    """Ingest every seeded law's roll-calls into the cache."""
    results = []
    for law in db.list_laws_with_keywords(conn):
        if log:
            log(f"Ingesting {law['label']} (proposição {law['camara_proposicao_id']})...")
        result = ingest_law(conn, law, pause=pause, limit_votes=limit_votes)
        if log:
            log(f"  -> {result['roll_calls']} roll-calls, {result['votes']} votes cached")
        results.append(result)
    return results
