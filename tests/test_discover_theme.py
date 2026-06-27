"""Find laws by theme (codTema) — the simple workflow from research/01.

topic = one or more codTema → /proposicoes?codTema=X → keep the voted bills.
"""
import discover_laws as dl


class FakeAPI:
    def __init__(self, routes):
        self.routes = routes

    def __call__(self, url):
        for fragment, payload in self.routes.items():
            if fragment in url:
                return payload
        return {"dados": []}


def test_search_by_themes_unions_and_filters_types():
    fake = FakeAPI({
        "codTema=70": {"dados": [
            {"id": 1, "siglaTipo": "PL", "numero": 4173, "ano": 2023, "ementa": "offshore", "uri": "u1"},
            {"id": 2, "siglaTipo": "REQ", "numero": 9, "ano": 2023, "ementa": "req", "uri": "u2"},
        ]},
        "codTema=40": {"dados": [
            {"id": 1, "siglaTipo": "PL", "numero": 4173, "ano": 2023, "ementa": "offshore", "uri": "u1"},
            {"id": 3, "siglaTipo": "PEC", "numero": 45, "ano": 2019, "ementa": "reforma", "uri": "u3"},
        ]},
    })
    props = dl.search_by_themes([70, 40], [2023, 2019], fetch=fake)
    assert sorted(p["id"] for p in props) == [1, 3]  # id=1 deduped, REQ filtered out


def test_discover_by_theme_keeps_only_voted():
    fake = FakeAPI({
        "codTema=70": {"dados": [
            {"id": 10, "siglaTipo": "PL", "numero": 1, "ano": 2023, "ementa": "voted", "uri": "a"},
            {"id": 11, "siglaTipo": "PL", "numero": 2, "ano": 2023, "ementa": "unvoted", "uri": "b"},
        ]},
        "proposicoes/10/votacoes": {"dados": [{"id": "v", "descricao": "Aprovada. Sim: 300; não: 100"}]},
        "proposicoes/11/votacoes": {"dados": [{"id": "w", "descricao": "Arquivada"}]},
    })
    laws = dl.discover_by_theme("tributacao-da-riqueza", [70], [2023], fetch=fake)
    assert [law["camara_proposicao_id"] for law in laws] == [10]
    assert laws[0]["topic_slug"] == "tributacao-da-riqueza"
