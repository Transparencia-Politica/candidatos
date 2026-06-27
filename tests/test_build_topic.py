"""build_topic: read a topic's cod_temas config -> discover -> store laws under it (append-only)."""
import db
import discover_laws as dl


class FakeAPI:
    def __init__(self, routes):
        self.routes = routes

    def __call__(self, url):
        for fragment, payload in self.routes.items():
            if fragment in url:
                return payload
        return {"dados": []}


def test_upsert_law_and_keyword_are_idempotent(conn):
    tid = db.get_topic(conn, "tributacao-da-riqueza")["id"]
    for label in ("PL X/2023", "PL X/2023 again"):
        db.upsert_law(conn, topic_id=tid, slug="pl-x-2023", camara_proposicao_id=999999,
                      label=label, kind="PL", number="X", year=2023, description="d",
                      source_url="u", is_key=0, wealth_relevant=1, sort_order=0)
    conn.commit()
    assert conn.execute("SELECT COUNT(*) AS n FROM laws WHERE slug='pl-x-2023'").fetchone()["n"] == 1

    lid = conn.execute("SELECT id FROM laws WHERE slug='pl-x-2023'").fetchone()["id"]
    for label in ("Trib", "Trib again"):
        db.upsert_keyword(conn, law_id=lid, slug="pl-x-2023-trib", label=label, description="d",
                          direction=1, weight=1.0, wealth_relevant=1, sort_order=0)
    conn.commit()
    assert conn.execute("SELECT COUNT(*) AS n FROM keywords WHERE slug='pl-x-2023-trib'").fetchone()["n"] == 1


def test_build_topic_discovers_by_config_and_stores_voted_laws(conn):
    fake = FakeAPI({
        "codTema=70": {"dados": [
            {"id": 501, "siglaTipo": "PL", "numero": 4173, "ano": 2023, "ementa": "offshore", "uri": "u"},
            {"id": 502, "siglaTipo": "PL", "numero": 9, "ano": 2023, "ementa": "unvoted", "uri": "u2"},
        ]},
        "proposicoes/501/votacoes": {"dados": [{"id": "v", "descricao": "Aprovada. Sim: 300; não: 100"}]},
        "proposicoes/502/votacoes": {"dados": [{"id": "w", "descricao": "Arquivada"}]},
    })
    result = dl.build_topic(conn, "tributacao-da-riqueza", [2023], fetch=fake)

    assert result["stored"] == 1  # only the voted bill
    laws = db.list_laws_with_keywords(conn)
    by_slug = {law["slug"]: law for law in laws}
    assert "pl-4173-2023" in by_slug
    assert by_slug["pl-4173-2023"]["keywords"]  # has at least one keyword (so it scores/shows)
