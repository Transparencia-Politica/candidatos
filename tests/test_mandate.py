"""Mandate-aware presence: only count roll-calls within the deputy's term window."""
import db
import score_candidate as sc
from conftest import law_id


def test_mandate_filter_excludes_votacoes_before_term(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    db.upsert_roll_call(conn, roll_call_id="old", law_id=lid, date="2021-09-01", description="Aprovada",
                      is_nominal=True, gov_orientation=None, opp_orientation=None)
    db.upsert_roll_call(conn, roll_call_id="new", law_id=lid, date="2023-10-25", description="Aprovada",
                      is_nominal=True, gov_orientation=None, opp_orientation=None)
    db.upsert_vote(conn, "new", 74478, "Sim")
    conn.commit()

    r_all = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r_all["nominal"] == 2 and r_all["present"] == 1

    r = sc.infer_law_vote_from_cache(conn, 74478, law, since_date="2023-02-01")
    assert r["nominal"] == 1 and r["present"] == 1


def test_mandate_filter_avoids_false_absence(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    db.upsert_roll_call(conn, roll_call_id="old", law_id=lid, date="2021-09-01", description="d",
                      is_nominal=True, gov_orientation=None, opp_orientation=None)
    conn.commit()  # deputy took office 2023, absent from this 2021 vote

    r = sc.infer_law_vote_from_cache(conn, 74478, law, since_date="2023-02-01")
    assert r["nominal"] == 0  # pre-term vote excluded -> not a missed vote
    assert r["vote_status"] == "sem-votacao-nominal"


def test_legislature_start_reads_datainicio():
    profile = {"ultimoStatus": {"idLegislatura": 57}}
    calls = []

    def fake(url):
        calls.append(url)
        return {"dados": {"dataInicio": "2023-02-01", "dataFim": "2027-01-31"}}

    assert sc.legislature_start(profile, fetch=fake) == "2023-02-01"
    assert "/legislaturas/57" in calls[0]
