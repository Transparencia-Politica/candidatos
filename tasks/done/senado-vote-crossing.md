# Wire Senado votes into the scoring strategy

Cross the existing laws with Senado (Senate) nominal roll-calls so **senators** become
scoreable against the same `laws` package, without polluting deputy scoring.

Demo target: **PEC 45/2019** (already seeded) — the one law in our set with clean nominal
Senado roll-calls (matéria 158930). Wealth-tax laws (PL 4173, PL 1087) cleared the Senate
**symbolically** (no nominal vote), so the honest finding is that crossing adds little
wealth-tax signal — proven, not hidden.

## Acceptance criteria

- [x] Verified Senado API contract documented in `research/14-senado-vote-crossing.md`; `INDEX.md` updated
- [x] Schema migration: `house` on `roll_calls`/`votes`, `senado_id`+`house` on `politics`, `camara_id` nullable — idempotent, MySQL-8.4-safe (no `ADD COLUMN IF NOT EXISTS`)
- [x] `get_law_roll_calls` / `get_deputy_votes` default to `house='camara'` so deputy scoring is unchanged (pollution guard on the denominator)
- [x] `app/senado.py`: find matéria, fetch nominal votações, cache roll-calls + votes (house='senado')
- [x] Score a senator on the cached laws from the senado cache (reuse `vote_class`/`score_keyword`)
- [x] CLI: `python app/senado.py --name "<senator>"` ingests + scores + prints the scorecard
- [x] Server endpoint returns a senator scorecard as JSON (curl/browser testable)
- [x] Tests: senado cache scoring works AND a deputy is NOT marked absent by senado roll-calls (pollution test). No network.
- [x] Full test suite green against dockerized MySQL; end-to-end run on one real senator
- [x] Report a real senator name the user can test with
