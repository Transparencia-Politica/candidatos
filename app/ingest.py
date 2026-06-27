#!/usr/bin/env python3
"""Ingest a law's roll-calls into the vote cache, once.

Roll-calls are deputy-independent and immutable, so a topic's laws are fetched a
single time and stored (votacoes/votos). Scoring then reads from the cache instead
of re-fetching per politician. See research/12-topic-packages-and-vote-caching.md.
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


def parse_orientation(orientacoes: list[dict[str, Any]], bloco_regex: str) -> str | None:
    for o in orientacoes:
        if re.search(bloco_regex, o.get("siglaPartidoBloco") or "", re.IGNORECASE):
            return o.get("orientacaoVoto")
    return None


def parse_votacao(
    votacao: dict[str, Any],
    votos: list[dict[str, Any]],
    orientacoes: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Pure: turn raw Câmara payloads into a votacao record + per-deputy voto rows."""
    record = {
        "votacao_id": str(votacao.get("id")),
        "date": votacao.get("data"),
        "description": votacao.get("descricao"),
        "is_nominal": bool(votos),
        "gov_orientation": parse_orientation(orientacoes, "governo"),
        "opp_orientation": parse_orientation(orientacoes, "oposi"),
    }
    rows = [
        {"camara_deputado_id": (r.get("deputado_") or {}).get("id"), "tipo_voto": r.get("tipoVoto")}
        for r in votos
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
    """Fetch a law's votações + per-deputy votos + government orientation, store in the cache.

    Only nominal roll-calls (non-empty /votos) are cached. Idempotent: re-ingesting
    upserts. `fetch` is injectable so the orchestration is testable without network.
    """
    law_id = law["id"]
    proposicao_id = law["camara_proposicao_id"]
    votacoes = fetch(
        f"{CAMARA}/proposicoes/{proposicao_id}/votacoes?ordem=DESC&ordenarPor=dataHoraRegistro"
    ).get("dados", [])

    stored_votacoes = 0
    stored_votos = 0
    for votacao in votacoes[:limit_votes]:
        vid = urllib.parse.quote(str(votacao.get("id")), safe="")
        votos = fetch(f"{CAMARA}/votacoes/{vid}/votos").get("dados", [])
        if not votos:
            continue  # symbolic vote — nothing to cache
        orientacoes = fetch(f"{CAMARA}/votacoes/{vid}/orientacoes").get("dados", [])
        record, voto_rows = parse_votacao(votacao, votos, orientacoes)
        db.upsert_votacao(
            conn,
            votacao_id=record["votacao_id"],
            law_id=law_id,
            date=record["date"],
            description=record["description"],
            is_nominal=record["is_nominal"],
            gov_orientation=record["gov_orientation"],
            opp_orientation=record["opp_orientation"],
        )
        for vr in voto_rows:
            db.upsert_voto(conn, record["votacao_id"], vr["camara_deputado_id"], vr["tipo_voto"])
        stored_votacoes += 1
        stored_votos += len(voto_rows)
        if pause:
            time.sleep(pause)

    conn.commit()
    return {"law_id": law_id, "votacoes": stored_votacoes, "votos": stored_votos}


def ingest_all(conn, *, pause: float = 0.35, limit_votes: int = 50, log: Callable | None = None) -> list[dict[str, Any]]:
    """Ingest every seeded law's roll-calls into the cache."""
    results = []
    for law in db.list_laws_with_keywords(conn):
        if log:
            log(f"Ingesting {law['label']} (proposição {law['camara_proposicao_id']})...")
        result = ingest_law(conn, law, pause=pause, limit_votes=limit_votes)
        if log:
            log(f"  -> {result['votacoes']} votações, {result['votos']} votos cached")
        results.append(result)
    return results
