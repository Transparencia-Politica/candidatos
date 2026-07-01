"""Government/Opposition alignment: how often a deputy votes with the Governo line."""
import db
import score_candidate as sc
from conftest import law_id


def test_infer_computes_gov_and_opp_alignment(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    db.upsert_roll_call(conn, roll_call_id="g1", law_id=lid, date="2023-05-01", description="d",
                      is_nominal=True, gov_orientation="Sim", opp_orientation="Não")
    db.upsert_roll_call(conn, roll_call_id="g2", law_id=lid, date="2023-05-02", description="d",
                      is_nominal=True, gov_orientation="Não", opp_orientation="Sim")
    db.upsert_roll_call(conn, roll_call_id="g3", law_id=lid, date="2023-05-03", description="d",
                      is_nominal=True, gov_orientation="Sim", opp_orientation="Não")
    for vid in ("g1", "g2", "g3"):
        db.upsert_vote(conn, vid, 74478, "Sim")
    conn.commit()

    r = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r["gov_comparable"] == 3
    assert r["gov_aligned"] == 2   # gov=Sim on g1,g3 (match); gov=Não on g2 (no)
    assert r["opp_comparable"] == 3
    assert r["opp_aligned"] == 1   # opp=Sim only on g2 (match)


def test_gov_alignment_ignores_non_directional_votes(conn):
    lid = law_id(conn, "pl-4173-2023")
    law = {"id": lid, "camara_proposicao_id": 2383287}
    db.upsert_roll_call(conn, roll_call_id="h1", law_id=lid, date="2023-05-01", description="d",
                      is_nominal=True, gov_orientation="Sim", opp_orientation="Não")
    db.upsert_roll_call(conn, roll_call_id="h2", law_id=lid, date="2023-05-02", description="d",
                      is_nominal=True, gov_orientation=None, opp_orientation=None)
    db.upsert_vote(conn, "h1", 74478, "Sim")
    db.upsert_vote(conn, "h2", 74478, "Sim")  # no gov orientation -> not comparable
    conn.commit()

    r = sc.infer_law_vote_from_cache(conn, 74478, law)
    assert r["gov_comparable"] == 1
    assert r["gov_aligned"] == 1


def test_summary_aggregates_gov_alignment_across_laws():
    politic = {"wealth_total": 100, "wealth_capital": 50}
    rows = [
        {"law_id": 1, "law_wealth_relevant": 1, "is_key": 1, "present_count": 2,
         "nominal_count": 3, "self_interest_value": None,
         "evidence_json": db.as_json({"gov_aligned": 2, "gov_comparable": 3})},
        {"law_id": 2, "law_wealth_relevant": 1, "is_key": 0, "present_count": 1,
         "nominal_count": 2, "self_interest_value": None,
         "evidence_json": db.as_json({"gov_aligned": 1, "gov_comparable": 1})},
    ]
    s = db._summary(politic, rows)
    assert s["gov_comparable_n"] == 4
    assert s["gov_alignment_pct"] == 75  # (2+1)/(3+1)


def test_summary_reports_weighted_confidence():
    politic = {"wealth_total": 100, "wealth_capital": 50}
    rows = [
        {"law_id": 1, "law_wealth_relevant": 1, "is_key": 1, "present_count": 1,
         "nominal_count": 1, "self_interest_value": None, "keyword_direction": 1,
         "keyword_weight": 1.5, "evidence_json": "{}"},
        {"law_id": 1, "law_wealth_relevant": 1, "is_key": 1, "present_count": 1,
         "nominal_count": 1, "self_interest_value": None, "keyword_direction": 1,
         "keyword_weight": 1.25, "evidence_json": "{}"},
        {"law_id": 2, "law_wealth_relevant": 1, "is_key": 0, "present_count": 0,
         "nominal_count": 1, "self_interest_value": None, "keyword_direction": 1,
         "keyword_weight": 1.5, "evidence_json": "{}"},
        {"law_id": 3, "law_wealth_relevant": 0, "is_key": 0, "present_count": 1,
         "nominal_count": 1, "self_interest_value": None, "keyword_direction": 0,
         "keyword_weight": 0.2, "evidence_json": "{}"},
    ]

    s = db._summary(politic, rows)

    assert s["coverage_pct"] == 50
    assert s["confidence_pct"] == 50
    assert s["confidence_weight_covered"] == 1.5
    assert s["confidence_weight_total"] == 3.0


def test_summary_splits_redistribution_from_self_interest():
    politic = {"wealth_total": 100, "wealth_capital": 50}
    rows = [
        {"law_id": 1, "law_wealth_relevant": 1, "is_key": 1, "present_count": 1,
         "nominal_count": 1, "score_value": 1.5, "self_interest_value": -1.5,
         "keyword_direction": 1, "keyword_weight": 1.5, "evidence_json": "{}"},
        {"law_id": 2, "law_wealth_relevant": 1, "is_key": 0, "present_count": 1,
         "nominal_count": 1, "score_value": -1.25, "self_interest_value": 1.25,
         "keyword_direction": 1, "keyword_weight": 1.25, "evidence_json": "{}"},
        {"law_id": 3, "law_wealth_relevant": 1, "is_key": 0, "present_count": 0,
         "nominal_count": 1, "score_value": -1.5, "self_interest_value": 1.5,
         "keyword_direction": 1, "keyword_weight": 1.5, "evidence_json": "{}"},
    ]

    s = db._summary(politic, rows)

    assert s["pro_redistribution_score"] == 55
    assert s["pro_redistribution_weight"] == 2.75
    assert s["self_interest_alignment_score"] == 45
    assert s["self_interest_weight"] == 2.75


def test_summary_aggregates_keywords_to_one_law_contribution():
    politic = {"wealth_total": 100, "wealth_capital": 50}
    rows = [
        {"law_id": 1, "law_wealth_relevant": 1, "is_key": 1, "present_count": 1,
         "nominal_count": 1, "score_id": 10, "score_value": 1.5,
         "self_interest_value": -1.5, "keyword_direction": 1, "keyword_weight": 1.5,
         "evidence_json": "{}"},
        {"law_id": 1, "law_wealth_relevant": 1, "is_key": 1, "present_count": 1,
         "nominal_count": 1, "score_id": 11, "score_value": -1.25,
         "self_interest_value": 1.25, "keyword_direction": 1, "keyword_weight": 1.25,
         "evidence_json": "{}"},
    ]

    rollup = db._law_rollup_row(rows)
    summary = db._summary(politic, rows)

    assert round(rollup["score_value"], 3) == 0.136
    assert rollup["_law_weight"] == 1.5
    assert summary["pro_redistribution_score"] == 55
    assert summary["pro_redistribution_weight"] == 1.5


def test_summary_exposes_vote_policy_contract():
    s = db._summary({"wealth_total": 0, "wealth_capital": 0}, [])

    assert "Sim/Não" in s["vote_policy"]["directional_votes"]
    assert "Abstenção" in s["vote_policy"]["neutral_votes"]
    assert "AUSENTE" in s["vote_policy"]["missing_votes"]
