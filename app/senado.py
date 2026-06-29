#!/usr/bin/env python3
"""Cross our seeded laws with Senado (Senate) nominal roll-calls and score a senator.

A federal bill is voted in *both* houses, so the same `law` row gathers Câmara *and* Senado
roll-calls. We find each law's Senado matéria by (sigla, número, ano) — the `kind/number/year`
we already store — cache its nominal votações like the Câmara package (research/12), and score a
senator from that cache. The Senado API contract is verified in
research/14-senado-vote-crossing.md.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

try:
    import db
    import score_candidate as sc
except ModuleNotFoundError:
    from app import db
    from app import score_candidate as sc


SENADO = "https://legis.senado.leg.br/dadosabertos"

# siglaVotoParlamentar values that mean the senator was present and cast a vote. Everything else
# (NCom = não compareceu, leaves/missions) is an absence: we don't store it, so the senator is
# correctly counted in the nominal denominator but not as present.
PRESENT_VOTES = {"Sim", "Não", "Nao", "Abstenção", "Abstencao", "Obstrução", "Obstrucao"}


def find_materia(kind: str, number: str, year: int) -> int | None:
    """Resolve a bill (e.g. PEC 45/2019) to its Senado matéria code, or None if not in the Senado."""
    url = f"{SENADO}/processo?sigla={kind}&numero={number}&ano={year}"
    rows = sc.fetch_json(url)
    if not isinstance(rows, list):
        return None
    for row in rows:
        if (
            str(row.get("siglaMateria") or row.get("sigla") or kind).upper() == kind.upper()
            and str(row.get("numeroMateria") or row.get("numero") or number).lstrip("0") == str(number).lstrip("0")
        ):
            return int(row["codigoMateria"])
    return int(rows[0]["codigoMateria"]) if rows else None


def fetch_votacoes(codigo_materia: int) -> list[dict[str, Any]]:
    """All votações of a matéria; nominal ones carry every senator's vote inline in `votos`."""
    data = sc.fetch_json(f"{SENADO}/votacao?codigoMateria={codigo_materia}")
    return data if isinstance(data, list) else []


def ingest_law(conn, law: dict[str, Any]) -> int:
    """Cache a law's nominal Senado roll-calls + every senator's vote. Returns roll-calls stored."""
    codigo = find_materia(law["kind"], law["number"], law["year"])
    if codigo is None:
        return 0
    stored = 0
    for vot in fetch_votacoes(codigo):
        if str(vot.get("votacaoSecreta") or "N").upper() == "S":
            continue  # secret vote: cannot attribute to a senator
        votos = vot.get("votos") or []
        if not votos:
            continue  # symbolic vote: no individual record (the "sem votação nominal" case)
        roll_call_id = f"sf-{vot['codigoSessaoVotacao']}"
        db.upsert_roll_call(
            conn,
            roll_call_id=roll_call_id,
            law_id=law["id"],
            date=vot.get("dataSessao"),
            description=vot.get("descricaoVotacao"),
            is_nominal=True,
            gov_orientation=None,  # Senado /votacao carries no Governo/Oposição line
            opp_orientation=None,
            house="senado",
        )
        for v in votos:
            sigla = (v.get("siglaVotoParlamentar") or "").strip()
            if sigla not in PRESENT_VOTES:
                continue
            db.upsert_vote(conn, roll_call_id, int(v["codigoParlamentar"]), sigla, house="senado")
        stored += 1
    conn.commit()
    return stored


def build_senado_package(conn, log=None) -> int:
    """Ingest Senado roll-calls for every seeded law. Idempotent — safe to re-run."""
    total = 0
    for law in db.list_laws_with_keywords(conn):
        n = ingest_law(conn, law)
        total += n
        if log:
            log(f"  {law['label']}: {n} nominal Senado roll-call(s)")
    return total


_SENATORS_CACHE: list[dict[str, Any]] = []


def list_current_senators(refresh: bool = False) -> list[dict[str, Any]]:
    """Current senators, cached in-process (the roster is stable within a server run)."""
    global _SENATORS_CACHE
    if _SENATORS_CACHE and not refresh:
        return _SENATORS_CACHE
    payload = sc.fetch_json(f"{SENADO}/senador/lista/atual")
    parlamentares = (
        payload.get("ListaParlamentarEmExercicio", {})
        .get("Parlamentares", {})
        .get("Parlamentar", [])
    )
    out = []
    for p in parlamentares:
        ident = p.get("IdentificacaoParlamentar", {})
        out.append(
            {
                "senado_id": int(ident["CodigoParlamentar"]),
                "name": ident.get("NomeParlamentar"),
                "full_name": ident.get("NomeCompletoParlamentar"),
                "party": ident.get("SiglaPartidoParlamentar") or "",
                "uf": ident.get("UfParlamentar") or "",
            }
        )
    _SENATORS_CACHE = out
    return out


def resolve_senator(name: str) -> dict[str, Any]:
    """Find a current senator by parliamentary or full name (accent/case-insensitive)."""
    target = sc.normalize_name(name)
    senators = list_current_senators()
    for s in senators:
        if sc.normalize_name(s["name"]) == target or sc.normalize_name(s.get("full_name")) == target:
            return s
    for s in senators:  # substring fallback
        if target in sc.normalize_name(s["name"]) or sc.normalize_name(s["name"]) in target:
            return s
    raise ValueError(f"No current senator matches '{name}'")


def score_senator(
    *, senado_id: int, name: str, party: str, uf: str, database_url: str | None = None,
    build_package: bool = True, init: bool = True, log=None
) -> dict[str, Any]:
    """Build the Senado package (once) and score this senator from the cache.

    `build_package=False` skips the (heavy) Senado roll-call ingest — the caller has already
    built it. A bulk roster scan builds the package once, then scores every senator with
    `build_package=False`, instead of re-ingesting all laws' Senado votações 81 times. The
    default keeps single-senator callers (server.py) behaving exactly as before. See research/15.
    """
    conn = db.init_db(database_url) if init else db.connect(database_url)
    try:
        if build_package:
            if log:
                log(f"Building Senado package for the seeded laws...")
            build_senado_package(conn, log=log)

        # Pull the senator's TSE declared wealth (bens), same machinery as deputies. Best-effort:
        # zeros if TSE can't resolve them, so a missing match never blocks the vote score.
        wealth = sc.senator_wealth(name, uf)
        if log:
            log(f"  wealth: R$ {wealth['wealth_total']:,.2f} "
                f"(TSE {wealth['tse_year'] or '—'}/{wealth['tse_uf'] or uf})")
        politic_id = db.upsert_senator(
            conn, senado_id=senado_id, name=name, party=party, uf=uf,
            wealth_total=wealth["wealth_total"], wealth_capital=wealth["wealth_capital"],
            wealth_buckets=wealth["buckets"], tse_sq=wealth["tse_sq"],
            tse_year=wealth["tse_year"], tse_uf=wealth["tse_uf"],
        )
        for law in db.list_laws_with_keywords(conn):
            law_vote = sc.infer_law_vote_from_cache(conn, senado_id, law, house="senado")
            for keyword in law["keywords"]:
                score_value, self_interest_value = sc.score_keyword(keyword, law_vote, wealth["wealth_capital"])
                evidence = {
                    "house": "senado",
                    "senado_votacao_ids": law_vote["nominal_vote_ids"],
                    "recorded_votes": law_vote["recorded"],
                    "all_recorded_vote_types": law_vote["votes"],
                    "passage_vote": law_vote["passage"],
                    "senado_source": f"{SENADO}/votacao?codigoMateria=<{law['kind']} {law['number']}/{law['year']}>",
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
                log(f"  -> {law['label']}: {law_vote['vote_label']} "
                    f"({law_vote['present']}/{law_vote['nominal']} votações nominais)")
        return {"politic_id": politic_id, "senado_id": senado_id, "name": name}
    finally:
        conn.close()


def run(args: argparse.Namespace) -> int:
    senator = resolve_senator(args.name)
    print(f"Senator: {senator['name']} ({senator['party']}-{senator['uf']}) "
          f"· Senado {senator['senado_id']}", flush=True)
    score_senator(
        senado_id=senator["senado_id"],
        name=senator["name"],
        party=senator["party"],
        uf=senator["uf"],
        database_url=args.db,
        log=lambda m: print(m, flush=True),
    )
    # Print the resulting scorecard so the run is self-verifying.
    conn = db.connect(args.db)
    try:
        cards = db.get_scorecards(conn, senado_id=senator["senado_id"])["scorecards"]
    finally:
        conn.close()
    if cards:
        card = cards[0]
        print(f"\nScorecard for {card['politic']['name']}:", flush=True)
        for topic in card["topics"]:
            for law in topic["laws"]:
                s = law.get("score") or {}
                print(f"  [{topic['title']}] {law['label']}: "
                      f"{s.get('vote_label', '—')} (score {s.get('score_value')})", flush=True)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=db.DATABASE_URL, help="Database URL; defaults to DATABASE_URL")
    p.add_argument("--name", default="Eduardo Braga", help="Senator name (parliamentary or full)")
    return p


if __name__ == "__main__":
    sys.exit(run(parser().parse_args()))
