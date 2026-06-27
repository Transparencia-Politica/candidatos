"""`snapshot.py site` bakes the assembled scorecards the static GitHub Pages page reads."""
import json

import snapshot


def test_export_site_writes_assembled_scorecards(conn, tmp_path):
    out_file = snapshot.export_site(conn, str(tmp_path))

    assert out_file.endswith("scorecards.json")
    payload = json.loads(open(out_file, encoding="utf-8").read())

    # Same top-level shape the frontend already renders from /api/scorecards.
    assert set(payload.keys()) == {"generated_at", "scorecards"}
    assert isinstance(payload["scorecards"], list)

    # Every card carries the three sections the static page renders.
    for card in payload["scorecards"]:
        assert set(card.keys()) >= {"politic", "summary", "topics"}
        assert "name" in card["politic"]
        assert "camara_id" in card["politic"]
        assert isinstance(card["topics"], list)
