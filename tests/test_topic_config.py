"""A topic carries its discovery config: the codTema(s) its laws live under."""
import db


def test_wealth_topic_seeded_with_cod_temas(conn):
    topic = db.get_topic(conn, "tributacao-da-riqueza")
    assert topic is not None
    assert topic["cod_temas"] == [70, 40, 68]


def test_get_topic_returns_none_for_unknown(conn):
    assert db.get_topic(conn, "does-not-exist") is None
