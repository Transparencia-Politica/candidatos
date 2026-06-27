"""Topic -> law discovery: keyword-descriptor search emitting curatable seed objects."""
import discover_laws as dl


class FakeAPI:
    def __init__(self, routes):
        self.routes = routes

    def __call__(self, url):
        for fragment, payload in self.routes.items():
            if fragment in url:
                return payload
        return {"dados": []}


def test_search_by_descriptors_dedups_and_filters_types():
    fake = FakeAPI({
        "keywords=dividendos": {"dados": [
            {"id": 1, "siglaTipo": "PL", "numero": 2337, "ano": 2021, "ementa": "IR", "uri": "u1"},
            {"id": 2, "siglaTipo": "REQ", "numero": 9, "ano": 2021, "ementa": "req", "uri": "u2"},
        ]},
        "keywords=ganho": {"dados": [
            {"id": 1, "siglaTipo": "PL", "numero": 2337, "ano": 2021, "ementa": "IR", "uri": "u1"},
            {"id": 3, "siglaTipo": "PEC", "numero": 45, "ano": 2019, "ementa": "reforma", "uri": "u3"},
        ]},
    })
    props = dl.search_by_descriptors(["dividendos", "ganho"], [2021, 2019], fetch=fake)
    assert sorted(p["id"] for p in props) == [1, 3]  # id=1 deduped, REQ filtered out


def test_to_seed_law_emits_seed_format():
    p = {"id": 2383287, "siglaTipo": "PL", "numero": 4173, "ano": 2023,
         "ementa": "Tributa renda no exterior", "uri": "http://x"}
    law = dl.to_seed_law("tributacao-da-riqueza", p)
    assert law["slug"] == "pl-4173-2023"
    assert law["camara_proposicao_id"] == 2383287
    assert law["label"] == "PL 4173/2023"
    assert law["kind"] == "PL" and law["year"] == 2023
    assert law["topic_slug"] == "tributacao-da-riqueza"
    assert law["description"] == "Tributa renda no exterior"


def test_discover_keeps_only_voted_bills():
    fake = FakeAPI({
        "keywords=dividendos": {"dados": [
            {"id": 10, "siglaTipo": "PL", "numero": 1, "ano": 2023, "ementa": "voted", "uri": "a"},
            {"id": 11, "siglaTipo": "PL", "numero": 2, "ano": 2023, "ementa": "unvoted", "uri": "b"},
        ]},
        "proposicoes/10/votacoes": {"dados": [{"id": "v", "descricao": "Aprovada. Sim: 300; não: 100"}]},
        "proposicoes/11/votacoes": {"dados": [{"id": "w", "descricao": "Arquivada"}]},
    })
    laws = dl.discover("tributacao-da-riqueza", ["dividendos"], [2023], fetch=fake)
    assert [law["camara_proposicao_id"] for law in laws] == [10]
