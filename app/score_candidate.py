#!/usr/bin/env python3
"""Fetch one politician, calculate keyword scores, and store them in MySQL."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    import db
except ModuleNotFoundError:
    from app import db


CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
TSE = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1"
DEFAULT_CANDIDATE = {
    "camara_id": 74478,
    "tse_year": 2022,
    "tse_uf": "PE",
    "tse_election_id": "2040602022",
    "tse_sq": "170001609112",
}


def fetch_json(url: str, attempts: int = 3, pause: float = 1.0) -> dict[str, Any]:
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
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts:
                raise
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == attempts:
                raise
        time.sleep(pause * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def br_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(".", "").replace(",", ".") if "," in str(value) else value)


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


def run(args: argparse.Namespace) -> int:
    conn = db.init_db(args.db)
    if args.seed_only:
        print(f"Seeded DB schema/reference data at {args.db or db.DB_PATH}")
        return 0

    profile = fetch_json(f"{CAMARA}/deputados/{args.camara_id}").get("dados", {})
    time.sleep(args.pause)
    tse_url = (
        f"{TSE}/candidatura/buscar/{args.tse_year}/{args.tse_uf}/"
        f"{args.tse_election_id}/candidato/{args.tse_sq}"
    )
    candidate = fetch_json(tse_url)
    status = profile.get("ultimoStatus") or {}
    assets = candidate.get("bens") or []
    buckets = bucketize_assets(assets)
    wealth_total = br_float(candidate.get("totalDeBens")) or sum(buckets.values())
    wealth_capital = buckets["Ações / participações"] + buckets["Depósito no exterior"]
    name = status.get("nome") or candidate.get("nomeUrna") or candidate.get("nomeCompleto") or f"Câmara {args.camara_id}"

    politic_id = db.upsert_politic(
        conn,
        camara_id=args.camara_id,
        tse_sq=args.tse_sq,
        tse_year=args.tse_year,
        tse_uf=args.tse_uf,
        tse_election_id=args.tse_election_id,
        name=name,
        party=status.get("siglaPartido") or candidate.get("partido") or "",
        uf=status.get("siglaUf") or args.tse_uf,
        birth_date=profile.get("dataNascimento"),
        occupation=candidate.get("ocupacao") or "",
        profile={"camara": profile, "tse": candidate},
        wealth_total=wealth_total,
        wealth_capital=wealth_capital,
        wealth_buckets=buckets,
    )

    for law in db.list_laws_with_keywords(conn):
        print(f"Scoring {name}: {law['label']}...", flush=True)
        law_vote = infer_law_vote(args.camara_id, law, args.limit_votes, args.pause)
        for keyword in law["keywords"]:
            score_value, self_interest_value = score_keyword(keyword, law_vote, wealth_capital)
            evidence = {
                "camara_votes_url": law_vote["source_url"],
                "camara_law_url": law["source_url"],
                "nominal_vote_ids": law_vote["nominal_vote_ids"],
                "recorded_votes": law_vote["recorded"],
                "all_recorded_vote_types": law_vote["votes"],
                "passage_vote": law_vote["passage"],
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
        print(f"  -> {law_vote['vote_label']} ({law_vote['present']}/{law_vote['nominal']} votações nominais)", flush=True)

    print(f"Stored scores for {name} in {args.db or db.DB_PATH}", flush=True)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=db.DATABASE_URL, help="Database URL; defaults to DATABASE_URL")
    p.add_argument("--camara-id", type=int, default=DEFAULT_CANDIDATE["camara_id"])
    p.add_argument("--tse-year", type=int, default=DEFAULT_CANDIDATE["tse_year"])
    p.add_argument("--tse-uf", default=DEFAULT_CANDIDATE["tse_uf"])
    p.add_argument("--tse-election-id", default=DEFAULT_CANDIDATE["tse_election_id"])
    p.add_argument("--tse-sq", default=DEFAULT_CANDIDATE["tse_sq"])
    p.add_argument("--limit-votes", type=int, default=25, help="Recent proposition votes to inspect per law")
    p.add_argument("--pause", type=float, default=0.35, help="Seconds to wait between public API calls")
    p.add_argument("--seed-only", action="store_true", help="Create schema and seed topics/laws/keywords only")
    return p


if __name__ == "__main__":
    sys.exit(run(parser().parse_args()))
