"""Crossing the Senado: senators score from senado roll-calls on the SAME laws, and senado
roll-calls must never pollute a deputy's (camara) scoring on the shared cache tables."""
import db
import score_candidate as sc
from conftest import law_id


def test_senado_cache_scoring_reads_only_senado_house(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287, "kind": "PL", "number": "4173", "year": 2023}
    db.upsert_roll_call(conn, roll_call_id="sf-1", law_id=lid, date="2023-12-13",
                        description="Aprovado o Projeto", is_nominal=True,
                        gov_orientation=None, opp_orientation=None, house="senado")
    db.upsert_vote(conn, "sf-1", 5672, "Sim", house="senado")  # a senator's codigoParlamentar
    conn.commit()

    r = sc.infer_law_vote_from_cache(conn, 5672, law, house="senado")
    assert r["nominal"] == 1
    assert r["present"] == 1
    assert r["stance"] == "Sim"
    assert r["vote_status"] == "sim"


def test_senado_rollcall_does_not_mark_a_deputy_absent(conn):
    """The pollution guard: a senado roll-call must not count toward a deputy's nominal
    denominator, or every deputy would be wrongly marked AUSENTE on senate-only votes."""
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287, "kind": "PL", "number": "4173", "year": 2023}
    # Only a SENADO roll-call exists for this law — no camara roll-calls at all.
    db.upsert_roll_call(conn, roll_call_id="sf-9", law_id=lid, date="2023-12-13",
                        description="Aprovado", is_nominal=True,
                        gov_orientation=None, opp_orientation=None, house="senado")
    db.upsert_vote(conn, "sf-9", 5672, "Sim", house="senado")
    conn.commit()

    # Scoring a DEPUTY (default house='camara') sees zero camara roll-calls -> not absent.
    r = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r["nominal"] == 0
    assert r["present"] == 0
    assert r["vote_status"] == "sem-votacao-nominal"


def test_deputy_and_senator_votes_do_not_cross(conn):
    lid = law_id(conn, "pl-4173-2023")
    db.upsert_roll_call(conn, roll_call_id="2383287-43", law_id=lid, date=None, description="d",
                        is_nominal=True, gov_orientation=None, opp_orientation=None, house="camara")
    db.upsert_roll_call(conn, roll_call_id="sf-2", law_id=lid, date=None, description="d",
                        is_nominal=True, gov_orientation=None, opp_orientation=None, house="senado")
    db.upsert_vote(conn, "2383287-43", 74478, "Não", house="camara")
    db.upsert_vote(conn, "sf-2", 74478, "Sim", house="senado")  # same numeric id, other house
    conn.commit()

    camara = db.get_deputy_votes(conn, camara_id=74478, law_ids=[lid], house="camara")
    senado = db.get_deputy_votes(conn, camara_id=74478, law_ids=[lid], house="senado")
    assert [v["vote_type"] for v in camara] == ["Não"]
    assert [v["vote_type"] for v in senado] == ["Sim"]


def test_upsert_senator_is_retrievable_by_senado_id(conn):
    pid = db.upsert_senator(conn, senado_id=5672, name="Alan Rick", party="REPUBLICANOS", uf="AC")
    conn.commit()
    cards = db.get_scorecards(conn, senado_id=5672)["scorecards"]
    assert len(cards) == 1
    p = cards[0]["politic"]
    assert p["name"] == "Alan Rick"
    assert p["house"] == "senado"
    assert p["camara_id"] is None
    assert p["senado_id"] == 5672
