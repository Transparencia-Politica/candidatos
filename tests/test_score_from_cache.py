"""Scoring reads each law's roll-calls from the cache (no per-politician API calls)."""
import db
import score_candidate as sc
from conftest import law_id


def _cache_pl4173(conn, lid):
    db.upsert_roll_call(conn, roll_call_id="x1", law_id=lid, date=None, description="Rejeitada emenda",
                      is_nominal=True, gov_orientation="Não", opp_orientation="Sim")
    db.upsert_roll_call(conn, roll_call_id="x2", law_id=lid, date=None, description="Aprovada a Subemenda",
                      is_nominal=True, gov_orientation="Sim", opp_orientation="Não")
    db.upsert_roll_call(conn, roll_call_id="x3", law_id=lid, date=None, description="Rejeitado requerimento",
                      is_nominal=True, gov_orientation="Não", opp_orientation="Sim")
    conn.commit()


def test_infer_from_cache_uses_passage_vote_and_counts_presence(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    _cache_pl4173(conn, lid)
    db.upsert_vote(conn, "x1", 74478, "Não")
    db.upsert_vote(conn, "x2", 74478, "Sim")  # the 'Aprovada' passage vote
    conn.commit()  # absent on x3

    r = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r["nominal"] == 3
    assert r["present"] == 2
    assert r["stance"] == "Sim"
    assert r["vote_status"] == "sim"


def test_infer_from_cache_marks_absent(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    _cache_pl4173(conn, lid)  # 3 roll-calls cached, deputy in none

    r = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r["nominal"] == 3
    assert r["present"] == 0
    assert r["vote_status"] == "ausente"


def test_infer_from_cache_makes_no_network_calls(conn, monkeypatch):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    _cache_pl4173(conn, lid)
    db.upsert_vote(conn, "x2", 74478, "Sim")
    conn.commit()

    def boom(*a, **k):
        raise AssertionError("scoring from cache must not call the API")
    monkeypatch.setattr(sc, "fetch_json", boom)

    r = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r["present"] == 1
