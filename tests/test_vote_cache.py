"""Vote-cache: store a law's roll-calls once, look up any deputy's vote from cache."""
from conftest import law_id


def test_get_deputy_votes_returns_cached_vote_with_orientation(conn):
    lid = law_id(conn, "pl-4173-2023")
    db_ = __import__("db")
    db_.upsert_votacao(
        conn, votacao_id="2383287-43", law_id=lid, date="2023-10-25",
        description="Aprovada a Subemenda Substitutiva Global",
        is_nominal=True, gov_orientation="Sim", opp_orientation="Não",
    )
    db_.upsert_voto(conn, votacao_id="2383287-43", camara_deputado_id=74478, tipo_voto="Não")
    db_.upsert_voto(conn, votacao_id="2383287-43", camara_deputado_id=99999, tipo_voto="Sim")
    conn.commit()

    votes = db_.get_deputy_votes(conn, camara_id=74478, law_ids=[lid])
    assert len(votes) == 1
    v = votes[0]
    assert v["votacao_id"] == "2383287-43"
    assert v["tipo_voto"] == "Não"
    assert v["law_id"] == lid
    assert v["gov_orientation"] == "Sim"


def test_upsert_voto_is_idempotent(conn):
    lid = law_id(conn, "pl-4173-2023")
    db_ = __import__("db")
    db_.upsert_votacao(conn, votacao_id="v1", law_id=lid, date=None, description="d",
                       is_nominal=True, gov_orientation=None, opp_orientation=None)
    db_.upsert_voto(conn, "v1", 74478, "Sim")
    db_.upsert_voto(conn, "v1", 74478, "Não")  # same PK -> update, not duplicate
    conn.commit()

    votes = db_.get_deputy_votes(conn, camara_id=74478, law_ids=[lid])
    assert len(votes) == 1
    assert votes[0]["tipo_voto"] == "Não"


def test_get_deputy_votes_only_returns_requested_laws(conn):
    lid1 = law_id(conn, "pl-4173-2023")
    lid2 = law_id(conn, "pl-2337-2021")
    db_ = __import__("db")
    db_.upsert_votacao(conn, votacao_id="a", law_id=lid1, date=None, description="",
                       is_nominal=True, gov_orientation=None, opp_orientation=None)
    db_.upsert_votacao(conn, votacao_id="b", law_id=lid2, date=None, description="",
                       is_nominal=True, gov_orientation=None, opp_orientation=None)
    db_.upsert_voto(conn, "a", 74478, "Sim")
    db_.upsert_voto(conn, "b", 74478, "Não")
    conn.commit()

    votes = db_.get_deputy_votes(conn, camara_id=74478, law_ids=[lid1])
    assert len(votes) == 1
    assert votes[0]["votacao_id"] == "a"
