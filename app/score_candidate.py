#!/usr/bin/env python3
"""Fetch one politician, calculate keyword scores, and store them in MySQL."""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any, Callable

try:
    import db
except ModuleNotFoundError:
    from app import db


CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
TSE = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1"
DEFAULT_ELECTION = {
    "tse_year": 2022,
    "tse_election_id": "2040602022",
    "tse_cargo": 6,
}
DEFAULT_CANDIDATE = {"camara_id": 74478}


# Telemetry hook: if set, called once per HTTP attempt with an event dict
# {host, status, ms, attempt, retry_after, error}. It's how a bulk run *learns* the APIs'
# throttling: every request (and every 429) is observable without coupling fetch_json to any
# particular logger. Default None = zero overhead and unchanged behavior for the UI/server.
REQUEST_HOOK: Callable[[dict[str, Any]], None] | None = None


def _emit(event: dict[str, Any]) -> None:
    hook = REQUEST_HOOK
    if hook is not None:
        try:
            hook(event)
        except Exception:
            pass  # telemetry must never break a fetch


def fetch_json(url: str, attempts: int = 5, pause: float = 1.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            ),
            "Referer": "https://divulgacandcontas.tse.jus.br/",
        },
    )
    host = urllib.parse.urlparse(url).hostname or ""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                body = response.read().decode("utf-8")
            _emit({"host": host, "status": getattr(response, "status", 200),
                   "ms": round((time.monotonic() - started) * 1000), "attempt": attempt})
            return json.loads(body)
        except urllib.error.HTTPError as exc:
            last_error = exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            _emit({"host": host, "status": exc.code,
                   "ms": round((time.monotonic() - started) * 1000), "attempt": attempt,
                   "retry_after": retry_after, "error": f"HTTP {exc.code}"})
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts:
                raise
            # Honor Retry-After on 429 when the server tells us; else exponential backoff + jitter.
            delay = float(retry_after) if (exc.code == 429 and retry_after and retry_after.isdigit()) \
                else pause * (2 ** (attempt - 1))
        except urllib.error.URLError as exc:
            last_error = exc
            _emit({"host": host, "status": None,
                   "ms": round((time.monotonic() - started) * 1000), "attempt": attempt,
                   "error": str(exc)})
            if attempt == attempts:
                raise
            delay = pause * (2 ** (attempt - 1))
        time.sleep(delay + random.uniform(0, 0.4))  # jitter avoids a synchronized retry stampede
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def normalize_name(value: str | None) -> str:
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.upper().split())


def search_deputies(name: str, limit: int = 10) -> list[dict[str, Any]]:
    data = fetch_json(f"{CAMARA}/deputados?nome={urllib.parse.quote(name)}&ordem=ASC&ordenarPor=nome").get("dados", [])
    return [
        {
            "camara_id": item.get("id"),
            "name": item.get("nome"),
            "party": item.get("siglaPartido"),
            "uf": item.get("siglaUf"),
            "photo_url": item.get("urlFoto"),
            "source_url": item.get("uri"),
        }
        for item in data[:limit]
    ]


def tse_candidates_from_response(payload: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    return payload.get("candidatos") or payload.get("dados") or []


@lru_cache(maxsize=None)
def _tse_listar(tse_year: int, tse_uf: str, tse_election_id: str, tse_cargo: int) -> tuple[dict[str, Any], ...]:
    """The full TSE candidate list for one (year, UF, election, cargo), memoized.

    A 2022 candidacy roster is immutable, so this never goes stale; memoizing it turns a
    bulk roster scan's per-candidate `listar` fetch (≈150 rows each, see research/15) into one
    call per UF. Both the deputy match (cargo 6) and the senator-wealth match (cargo 5) route
    through here, so the cache helps both houses. Exceptions are never cached (lru_cache skips
    them), so a transient TSE failure is retried on the next call.
    """
    url = f"{TSE}/candidatura/listar/{tse_year}/{tse_uf}/{tse_election_id}/{tse_cargo}/candidatos"
    return tuple(tse_candidates_from_response(fetch_json(url)))


def resolve_tse_candidate(
    profile: dict[str, Any],
    *,
    tse_year: int,
    tse_uf: str,
    tse_election_id: str,
    tse_cargo: int,
) -> tuple[dict[str, Any], str]:
    status = profile.get("ultimoStatus") or {}
    names = [
        normalize_name(status.get("nome")),
        normalize_name(profile.get("nomeCivil")),
        normalize_name(profile.get("nome")),
    ]
    names = [name for name in names if name]
    candidates = _tse_listar(tse_year, tse_uf, tse_election_id, tse_cargo)

    def candidate_names(candidate: dict[str, Any]) -> list[str]:
        return [
            normalize_name(candidate.get("nomeUrna")),
            normalize_name(candidate.get("nomeCompleto")),
            normalize_name(candidate.get("nome")),
        ]

    for candidate in candidates:
        indexed_names = candidate_names(candidate)
        if any(name and name in indexed_names for name in names):
            return fetch_tse_detail(tse_year, tse_uf, tse_election_id, str(candidate["id"])), str(candidate["id"])

    for candidate in candidates:
        indexed_names = [name for name in candidate_names(candidate) if name]
        if any(name in indexed or indexed in name for name in names for indexed in indexed_names):
            return fetch_tse_detail(tse_year, tse_uf, tse_election_id, str(candidate["id"])), str(candidate["id"])

    raise ValueError(f"TSE candidate not found for {status.get('nome') or profile.get('nome')} in {tse_uf}/{tse_year}")


def fetch_tse_detail(tse_year: int, tse_uf: str, tse_election_id: str, tse_sq: str) -> dict[str, Any]:
    return fetch_json(f"{TSE}/candidatura/buscar/{tse_year}/{tse_uf}/{tse_election_id}/candidato/{tse_sq}")


def br_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(".", "").replace(",", ".") if "," in str(value) else value)


# Senators serve 8-year staggered terms, so a sitting senator was elected in 2018 or 2022.
# TSE cargo 5 = Senador. Only the 2022 general código (2040602022) is verified live against
# DivulgaCandContas; the 2018 código isn't resolvable through this REST API (elections-list routes
# 404, candidate-list returns empty for the códigos tried), so 2018-elected senators fall through
# to "wealth not found" until we wire the TSE bulk dataset. See research/14.
SENATOR_ELECTIONS = [(2022, "2040602022")]


def resolve_tse_senator(
    name: str, uf: str, elections: list[tuple[int, str]] = SENATOR_ELECTIONS
) -> tuple[dict[str, Any], int, str, str] | None:
    """Find a senator's TSE candidacy (cargo 5) across their possible election years, by name+UF.

    Returns (detail, tse_year, tse_election_id, tse_sq) or None if not resolvable. Best-effort:
    a TSE outage or an unmatched name yields None, never an exception that breaks scoring.
    """
    target = normalize_name(name)
    for year, eid in elections:
        try:
            cands = _tse_listar(year, uf, eid, 5)
        except Exception:
            continue
        for c in cands:
            names = [n for n in (normalize_name(c.get("nomeUrna")), normalize_name(c.get("nomeCompleto"))) if n]
            if target in names or any(target in n or n in target for n in names):
                try:
                    return fetch_tse_detail(year, uf, eid, str(c["id"])), year, eid, str(c["id"])
                except Exception:
                    return None
    return None


def senator_wealth(name: str, uf: str) -> dict[str, Any]:
    """Best-effort TSE bens for a senator. Zeros (and null provenance) if not resolvable."""
    empty = {"wealth_total": 0.0, "wealth_capital": 0.0, "buckets": {},
             "tse_sq": None, "tse_year": None, "tse_uf": None}
    resolved = resolve_tse_senator(name, uf)
    if not resolved:
        return empty
    detail, year, _eid, sq = resolved
    buckets = bucketize_assets(detail.get("bens") or [])
    total = br_float(detail.get("totalDeBens")) or sum(buckets.values())
    capital = buckets["Ações / participações"] + buckets["Depósito no exterior"]
    return {"wealth_total": total, "wealth_capital": capital, "buckets": buckets,
            "tse_sq": sq, "tse_year": year, "tse_uf": uf}


def bucketize_assets(assets: list[dict[str, Any]]) -> dict[str, float]:
    buckets = {
        "Ações / participações": 0.0,
        "Depósito no exterior": 0.0,
        "Dinheiro em espécie": 0.0,
        "Poupança / renda fixa / contas": 0.0,
        "Outros": 0.0,
    }
    for asset in assets or []:
        value = br_float(asset.get("valor"))
        desc = (asset.get("descricaoDeTipoDeBem") or "").lower()
        if any(token in desc for token in ("ações", "acoes", "quota", "participa")):
            buckets["Ações / participações"] += value
        elif "exterior" in desc:
            buckets["Depósito no exterior"] += value
        elif "espécie" in desc or "especie" in desc:
            buckets["Dinheiro em espécie"] += value
        elif any(token in desc for token in ("poupança", "poupanca", "renda fixa", "depósito", "deposito", "cdb")):
            buckets["Poupança / renda fixa / contas"] += value
        else:
            buckets["Outros"] += value
    return buckets


def vote_sign(stance: str | None) -> int | None:
    if stance == "Sim":
        return 1
    if stance == "Não":
        return -1
    if stance in ("Abstenção", "Obstrução", "Artigo 17"):
        return 0
    return None


def vote_class(stance: str | None, nominal: int, present: int, votes: list[str]) -> tuple[str, str, str | None]:
    if nominal == 0:
        return "sem-votacao-nominal", "sem votação nominal", None
    if present == 0:
        return "ausente", "AUSENTE", None
    if stance:
        return stance.lower().replace("ã", "a").replace("ç", "c"), stance.upper(), stance
    distinct = sorted(set(votes))
    if len(distinct) == 1:
        only = distinct[0]
        return only.lower().replace("ã", "a").replace("ç", "c"), only.upper(), only
    return "misto", f"MISTO ({len(votes)} votos)", None


def infer_law_vote(camara_id: int, law: dict[str, Any], limit_votes: int, pause: float) -> dict[str, Any]:
    url = f"{CAMARA}/proposicoes/{law['camara_proposicao_id']}/votacoes?ordem=DESC&ordenarPor=dataHoraRegistro"
    fetch_error = None
    try:
        votacoes = fetch_json(url).get("dados", [])
    except Exception as exc:
        votacoes = []
        fetch_error = str(exc)
    present = 0
    nominal = 0
    votes: list[str] = []
    recorded: list[dict[str, Any]] = []
    passage: str | None = None
    nominal_vote_ids: list[str] = []

    for vote in votacoes[:limit_votes]:
        time.sleep(pause)
        vote_id = vote.get("id")
        vote_url = f"{CAMARA}/votacoes/{urllib.parse.quote(str(vote_id), safe='')}/votos"
        try:
            vote_rows = fetch_json(vote_url).get("dados", [])
        except Exception as exc:
            recorded.append({"vote_id": vote_id, "error": str(exc)})
            continue
        if not vote_rows:
            continue
        nominal += 1
        nominal_vote_ids.append(str(vote_id))
        mine = next(
            (
                row for row in vote_rows
                if (row.get("deputado_") or {}).get("id") == camara_id
            ),
            None,
        )
        if mine:
            tipo = mine.get("tipoVoto")
            present += 1
            votes.append(tipo)
            recorded.append(
                {
                    "vote_id": vote_id,
                    "date": vote.get("data"),
                    "description": vote.get("descricao"),
                    "tipo_voto": tipo,
                }
            )
            if tipo and re.search("aprovad", vote.get("descricao") or "", re.IGNORECASE) and passage is None:
                passage = tipo

    selected_stance = passage if passage else (votes[0] if len(set(votes)) == 1 and votes else None)
    vote_status, vote_label, stance = vote_class(selected_stance, nominal, present, votes)
    return {
        "present": present,
        "nominal": nominal,
        "votes": votes,
        "passage": passage,
        "stance": stance,
        "vote_status": vote_status,
        "vote_label": vote_label,
        "nominal_vote_ids": nominal_vote_ids,
        "recorded": recorded,
        "source_url": url,
        "fetch_error": fetch_error,
    }


def legislature_start(profile: dict[str, Any], fetch=fetch_json) -> str | None:
    """Start date (ISO) of the deputy's current legislature, for mandate-aware presence."""
    leg = (profile.get("ultimoStatus") or {}).get("idLegislatura")
    if not leg:
        return None
    try:
        return (fetch(f"{CAMARA}/legislaturas/{leg}").get("dados") or {}).get("dataInicio")
    except Exception:
        return None


def infer_law_vote_from_cache(
    conn, camara_id: int, law: dict[str, Any], since_date: str | None = None, house: str = "camara"
) -> dict[str, Any]:
    """Compute present/nominal/stance for a voter from the stored vote cache — no API calls.

    The cache holds every voter's vote on each of a law's nominal roll-calls, so this is
    a pure DB lookup. When `since_date` (ISO) is given, only roll-calls on/after it are
    counted — so a voter is never marked absent for votes before their term began.
    `house` ('camara'|'senado') scopes both the roll-calls (the nominal denominator) and the
    voter's votes to one chamber, so deputies and senators never cross-pollute the same law's
    stored roll-calls. See research/12 and research/13.
    """
    roll_calls = db.get_law_roll_calls(conn, law["id"], house=house)
    if since_date:
        roll_calls = [v for v in roll_calls if (v.get("date") or "") >= since_date]
    nominal = len(roll_calls)
    valid_ids = {v["id"] for v in roll_calls}
    desc_by_id = {v["id"]: (v.get("description") or "") for v in roll_calls}

    mine = db.get_deputy_votes(conn, camara_id=camara_id, law_ids=[law["id"]], house=house)
    if since_date:
        mine = [m for m in mine if m["roll_call_id"] in valid_ids]
    present = len(mine)
    votes: list[str] = []
    recorded: list[dict[str, Any]] = []
    passage: str | None = None
    gov_aligned = gov_comparable = 0
    opp_aligned = opp_comparable = 0
    for row in mine:
        vote_type = row["vote_type"]
        votes.append(vote_type)
        recorded.append({"roll_call_id": row["roll_call_id"], "vote_type": vote_type})
        if vote_type and re.search("aprovad", desc_by_id.get(row["roll_call_id"], ""), re.IGNORECASE) and passage is None:
            passage = vote_type
        # government/opposition alignment: only over directional (Sim/Não) votes with a defined line
        if vote_type in ("Sim", "Não"):
            if row.get("gov_orientation") in ("Sim", "Não"):
                gov_comparable += 1
                if vote_type == row["gov_orientation"]:
                    gov_aligned += 1
            if row.get("opp_orientation") in ("Sim", "Não"):
                opp_comparable += 1
                if vote_type == row["opp_orientation"]:
                    opp_aligned += 1

    selected_stance = passage if passage else (votes[0] if len(set(votes)) == 1 and votes else None)
    vote_status, vote_label, stance = vote_class(selected_stance, nominal, present, votes)
    return {
        "present": present,
        "nominal": nominal,
        "votes": votes,
        "passage": passage,
        "stance": stance,
        "vote_status": vote_status,
        "vote_label": vote_label,
        "nominal_vote_ids": [v["id"] for v in roll_calls],
        "recorded": recorded,
        "gov_aligned": gov_aligned,
        "gov_comparable": gov_comparable,
        "opp_aligned": opp_aligned,
        "opp_comparable": opp_comparable,
        "source_url": f"{CAMARA}/proposicoes/{law['camara_proposicao_id']}/votacoes",
        "fetch_error": None,
    }


def score_keyword(keyword: dict[str, Any], law_vote: dict[str, Any], wealth_capital: float) -> tuple[float | None, float | None]:
    sign = vote_sign(law_vote["stance"])
    if sign is None:
        return None, None
    direction = int(keyword["direction"])
    score_value = 0.0 if direction == 0 else float(sign * direction)
    self_interest_value = None
    if keyword["wealth_relevant"] and wealth_capital > 0 and direction != 0:
        self_interest_value = -score_value
    return score_value, self_interest_value


def score_camara_candidate(
    *,
    camara_id: int,
    database_url: str | None = None,
    tse_year: int = DEFAULT_ELECTION["tse_year"],
    tse_uf: str | None = None,
    tse_election_id: str = DEFAULT_ELECTION["tse_election_id"],
    tse_cargo: int = DEFAULT_ELECTION["tse_cargo"],
    tse_sq: str | None = None,
    limit_votes: int = 25,
    pause: float = 0.35,
    init: bool = True,
    log=None,
) -> dict[str, Any]:
    # `init=False` skips schema-create + reference seed (use a plain connection). A parallel
    # roster scan seeds ONCE up front, then runs workers with init=False — otherwise N threads
    # each re-run the seed's `ON DUPLICATE KEY UPDATE` on the same topic/law rows and deadlock in
    # InnoDB. Default True keeps single-shot callers (server.py, CLI) behaving exactly as before.
    conn = db.init_db(database_url) if init else db.connect(database_url)
    try:
        profile = fetch_json(f"{CAMARA}/deputados/{camara_id}").get("dados", {})
        status = profile.get("ultimoStatus") or {}
        tse_uf = tse_uf or status.get("siglaUf")
        if not tse_uf:
            raise ValueError(f"Cannot infer TSE UF for Câmara id {camara_id}")
        time.sleep(pause)
        candidate: dict[str, Any] = {}
        try:
            if tse_sq:
                candidate = fetch_tse_detail(tse_year, tse_uf, tse_election_id, tse_sq)
            else:
                candidate, tse_sq = resolve_tse_candidate(
                    profile,
                    tse_year=tse_year,
                    tse_uf=tse_uf,
                    tse_election_id=tse_election_id,
                    tse_cargo=tse_cargo,
                )
        except Exception as exc:
            # TSE candidacy not matchable (name mismatch, suplente sworn in mid-term, off-year
            # election). Don't discard the deputy + their vote scores over a *wealth* lookup —
            # keep them with tse_sq=None so the UI shows wealth as '—' (never a fabricated R$ 0).
            tse_sq = None
            if log:
                log(f"  TSE wealth unresolved for Câmara {camara_id} ({tse_uf}): {exc}")
        tse_url = (f"{TSE}/candidatura/buscar/{tse_year}/{tse_uf}/{tse_election_id}/candidato/{tse_sq}"
                   if tse_sq else None)
        assets = candidate.get("bens") or []
        buckets = bucketize_assets(assets)
        wealth_total = br_float(candidate.get("totalDeBens")) or sum(buckets.values())
        wealth_capital = buckets["Ações / participações"] + buckets["Depósito no exterior"]
        name = status.get("nome") or candidate.get("nomeUrna") or candidate.get("nomeCompleto") or f"Câmara {camara_id}"

        politic_id = db.upsert_politic(
            conn,
            camara_id=camara_id,
            tse_sq=tse_sq,
            tse_year=tse_year,
            tse_uf=tse_uf,
            tse_election_id=tse_election_id,
            name=name,
            party=status.get("siglaPartido") or candidate.get("partido") or "",
            uf=status.get("siglaUf") or tse_uf,
            birth_date=profile.get("dataNascimento"),
            occupation=candidate.get("ocupacao") or "",
            profile={"camara": profile, "tse": candidate},
            wealth_total=wealth_total,
            wealth_capital=wealth_capital,
            wealth_buckets=buckets,
        )

        since_date = legislature_start(profile)
        for law in db.list_laws_with_keywords(conn):
            if log:
                log(f"Scoring {name}: {law['label']}...")
            law_vote = infer_law_vote_from_cache(conn, camara_id, law, since_date=since_date)
            for keyword in law["keywords"]:
                score_value, self_interest_value = score_keyword(keyword, law_vote, wealth_capital)
                evidence = {
                    "camara_votes_url": law_vote["source_url"],
                    "camara_law_url": law["source_url"],
                    "nominal_vote_ids": law_vote["nominal_vote_ids"],
                    "recorded_votes": law_vote["recorded"],
                    "all_recorded_vote_types": law_vote["votes"],
                    "passage_vote": law_vote["passage"],
                    "gov_aligned": law_vote["gov_aligned"],
                    "gov_comparable": law_vote["gov_comparable"],
                    "opp_aligned": law_vote["opp_aligned"],
                    "opp_comparable": law_vote["opp_comparable"],
                    "tse_candidate_url": tse_url,
                    "fetch_error": law_vote["fetch_error"],
                }
                db.upsert_score(
                    conn,
                    politic_id=politic_id,
                    keyword_id=keyword["id"],
                    score_value=score_value,
                    self_interest_value=self_interest_value,
                    vote_status=law_vote["vote_status"],
                    vote_label=law_vote["vote_label"],
                    stance=law_vote["stance"],
                    present_count=law_vote["present"],
                    nominal_count=law_vote["nominal"],
                    coverage_value=1.0 if law_vote["present"] > 0 else 0.0,
                    evidence=evidence,
                )
            conn.commit()
            if log:
                log(f"  -> {law_vote['vote_label']} ({law_vote['present']}/{law_vote['nominal']} votações nominais)")

        return {"politic_id": politic_id, "camara_id": camara_id, "name": name, "tse_sq": tse_sq}
    finally:
        conn.close()


def run(args: argparse.Namespace) -> int:
    if args.seed_only:
        conn = db.init_db(args.db)
        conn.close()
        print(f"Seeded MySQL schema/reference data at {args.db or db.DATABASE_URL}")
        return 0

    result = score_camara_candidate(
        camara_id=args.camara_id,
        database_url=args.db,
        tse_year=args.tse_year,
        tse_uf=args.tse_uf,
        tse_election_id=args.tse_election_id,
        tse_cargo=args.tse_cargo,
        tse_sq=args.tse_sq,
        limit_votes=args.limit_votes,
        pause=args.pause,
        log=lambda message: print(message, flush=True),
    )
    name = result["name"]
    print(f"Stored scores for {name} in {args.db or db.DATABASE_URL}", flush=True)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=db.DATABASE_URL, help="Database URL; defaults to DATABASE_URL")
    p.add_argument("--camara-id", type=int, default=DEFAULT_CANDIDATE["camara_id"])
    p.add_argument("--tse-year", type=int, default=DEFAULT_ELECTION["tse_year"])
    p.add_argument("--tse-uf")
    p.add_argument("--tse-election-id", default=DEFAULT_ELECTION["tse_election_id"])
    p.add_argument("--tse-cargo", type=int, default=DEFAULT_ELECTION["tse_cargo"])
    p.add_argument("--tse-sq")
    p.add_argument("--limit-votes", type=int, default=25, help="Recent proposition votes to inspect per law")
    p.add_argument("--pause", type=float, default=0.35, help="Seconds to wait between public API calls")
    p.add_argument("--seed-only", action="store_true", help="Create schema and seed topics/laws/keywords only")
    return p


if __name__ == "__main__":
    sys.exit(run(parser().parse_args()))
