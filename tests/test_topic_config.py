"""A topic carries its discovery config: the codTema(s) its laws live under."""
import db


def test_wealth_topic_seeded_with_cod_temas(conn):
    topic = db.get_topic(conn, "tributacao-da-riqueza")
    assert topic is not None
    assert topic["cod_temas"] == [70, 40, 68]


def test_get_topic_returns_none_for_unknown(conn):
    assert db.get_topic(conn, "does-not-exist") is None


def test_wealth_tax_keywords_use_tiered_weights(conn):
    rows = conn.execute("SELECT slug, direction, weight, wealth_relevant FROM keywords").fetchall()
    keywords = {row["slug"]: row for row in rows}

    assert keywords["igf-patrimonio"]["weight"] == db.WEIGHT_VERY_HIGH
    assert keywords["offshore"]["weight"] == db.WEIGHT_VERY_HIGH
    assert keywords["fundos-exclusivos"]["weight"] == db.WEIGHT_VERY_HIGH
    assert keywords["imposto-minimo-super-ricos"]["weight"] == db.WEIGHT_VERY_HIGH
    assert keywords["dividendos"]["weight"] == db.WEIGHT_HIGH
    assert keywords["tributacao-do-consumo"]["weight"] == db.WEIGHT_CONTEXT
    assert keywords["tributacao-do-consumo"]["direction"] == 0
    assert not keywords["tributacao-do-consumo"]["wealth_relevant"]


def test_wealth_tax_signature_package_is_curated(conn):
    rows = conn.execute(
        """
        SELECT t.slug AS topic_slug, l.slug, l.is_key, l.wealth_relevant, k.slug AS keyword_slug
        FROM laws l
        JOIN topics t ON t.id = l.topic_id
        JOIN keywords k ON k.law_id = l.id
        ORDER BY l.sort_order, k.sort_order
        """
    ).fetchall()
    wealth_laws = {
        row["slug"]
        for row in rows
        if row["topic_slug"] == "tributacao-da-riqueza"
    }
    context_laws = {
        row["slug"]
        for row in rows
        if row["topic_slug"] == "reforma-tributaria"
    }
    key_laws = {row["slug"] for row in rows if row["is_key"]}
    wealth_keywords = {row["keyword_slug"] for row in rows if row["wealth_relevant"]}

    assert wealth_laws == {
        "igf-grandes-fortunas",
        "pl-4173-2023",
        "pl-1087-2025",
        "pl-2337-2021",
    }
    assert context_laws == {"pec-45-2019"}
    assert key_laws == {"igf-grandes-fortunas", "pl-4173-2023", "pl-1087-2025"}
    assert wealth_keywords == {
        "igf-patrimonio",
        "offshore",
        "fundos-exclusivos",
        "imposto-minimo-super-ricos",
        "dividendos",
    }
