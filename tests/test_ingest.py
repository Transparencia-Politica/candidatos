"""Ingestion: fetch a law's roll-calls once and store them in the vote cache."""
import db
import ingest
from conftest import law_id


class FakeAPI:
    """Injected stand-in for fetch_json: matches a URL by substring → canned payload."""
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        for fragment, payload in self.routes.items():
            if fragment in url:
                return payload
        raise AssertionError(f"no fake route for {url}")


def test_parse_votacao_extracts_orientation_and_votes():
    votacao = {"id": "2383287-43", "data": "2023-10-25", "descricao": "Aprovada a Subemenda"}
    votos = [
        {"tipoVoto": "Não", "deputado_": {"id": 74478}},
        {"tipoVoto": "Sim", "deputado_": {"id": 99999}},
    ]
    orientacoes = [
        {"siglaPartidoBloco": "Governo", "orientacaoVoto": "Sim"},
        {"siglaPartidoBloco": "Oposição", "orientacaoVoto": "Não"},
    ]
    record, rows = ingest.parse_votacao(votacao, votos, orientacoes)
    assert record["votacao_id"] == "2383287-43"
    assert record["is_nominal"] is True
    assert record["gov_orientation"] == "Sim"
    assert record["opp_orientation"] == "Não"
    assert {"camara_deputado_id": 74478, "tipo_voto": "Não"} in rows
    assert len(rows) == 2


def test_ingest_law_caches_nominal_rollcalls_and_skips_symbolic(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    fake = FakeAPI({
        "proposicoes/2383287/votacoes": {"dados": [
            {"id": "v-nom", "data": "2023-10-25", "descricao": "Aprovada"},
            {"id": "v-sym", "descricao": "Votação simbólica"},
        ]},
        "votacoes/v-nom/votos": {"dados": [{"tipoVoto": "Não", "deputado_": {"id": 74478}}]},
        "votacoes/v-nom/orientacoes": {"dados": [{"siglaPartidoBloco": "Governo", "orientacaoVoto": "Sim"}]},
        "votacoes/v-sym/votos": {"dados": []},
    })

    result = ingest.ingest_law(conn, law, fetch=fake, pause=0)

    assert result["votacoes"] == 1  # symbolic (empty votos) is skipped
    cached = db.get_deputy_votes(conn, camara_id=74478, law_ids=[lid])
    assert len(cached) == 1
    assert cached[0]["votacao_id"] == "v-nom"
    assert cached[0]["tipo_voto"] == "Não"
    assert cached[0]["gov_orientation"] == "Sim"


def test_ingest_law_is_idempotent(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    fake = FakeAPI({
        "proposicoes/2383287/votacoes": {"dados": [{"id": "v-nom", "descricao": "Aprovada"}]},
        "votacoes/v-nom/votos": {"dados": [{"tipoVoto": "Sim", "deputado_": {"id": 74478}}]},
        "votacoes/v-nom/orientacoes": {"dados": []},
    })
    ingest.ingest_law(conn, law, fetch=fake, pause=0)
    ingest.ingest_law(conn, law, fetch=fake, pause=0)  # re-ingest must not duplicate
    cached = db.get_deputy_votes(conn, camara_id=74478, law_ids=[lid])
    assert len(cached) == 1
