# Scoring Improvements Tracker

*Implementation tracker for improving the current wealth-tax scoring pipeline with the tools already in this repo. Compiled on 2026-07-01 from a read of `app/db.py`, `app/score_candidate.py`, `docs/DATABASE.md`, and the existing wealth-tax POC notes.*

This tracker is deliberately scoped to the **current** architecture:

```text
topics -> laws -> keywords -> scores <- politics
```

The goal is not a new methodology from scratch. The goal is to make the existing wealth-tax
score more defensible by using primitives the code already has: `direction`, `weight`,
`wealth_relevant`, asset buckets, roll-call cache metadata, and per-law coverage.

---

## Conversational explanation

The current system already has the right basic pieces, but it still treats too many things as if
they were equally informative. A vote on an IGF proposal, a vote on offshore wealth, and a broad
tax-reform context vote should not all carry the same political meaning. The next scoring pass
should make that explicit.

For the wealth-tax theme, the score should answer one primary question and keep one contextual
signal separate:

- Did this politician vote in favor of taxing concentrated wealth?
- When this politician has declared assets that overlap with the taxed base, is that overlap useful
  context for reading the vote?

Those two pieces should stay separate. The public score is about the policy direction of the vote:
tributação progressiva versus proteção da concentração de riqueza. Asset overlap is context about
the declared asset base, not a claim about motive. Combining them too early makes the result harder
to defend.

The better model with today's tools is:

```text
law_score = vote_sign * direction * weight

topic_score = sum(weighted law scores with recorded votes)
              / sum(weights for covered laws)

confidence = covered_weight / total_possible_weight

asset_exposure_context = law_score * exposure_to_affected_asset_class
```

In plain terms: first decide whether the law really moves policy toward taxing wealth. Then decide
how important that law is for the theme. Then check how the politician voted. Finally, show asset
overlap only as context when the politician's declared assets overlap with the taxed base.

For a Zucman-inspired wealth-tax rubric, that means:

- IGF / large-fortune taxation should carry very high weight.
- Offshore wealth and exclusive-fund taxation should carry very high weight.
- Dividends, capital income, and minimum taxes on very high incomes should carry high weight.
- Broad consumption-tax reform should be context, not strong evidence about wealth taxation.
- Missing votes should reduce confidence, not silently become a political position.

The honest public claim is therefore: the current law package and directions are broadly compatible
with a Zucman-style view of wealth concentration, but the implementation is still a first-pass
heuristic. To make the score stronger, the code needs to use `weight`, aggregate by law, expose
confidence, and scale asset-exposure context by the affected tax base.

---

## Current baseline

What the code already does today:

- Seeds a curated set of wealth-tax laws and keywords in `app/db.py`.
- Resolves a politician against Câmara / Senado + TSE declared assets.
- Infers one law-level stance from cached nominal roll-calls.
- Scores each keyword as `vote_sign × direction`.
- Derives `self_interest_value` as the inverse of the score when the candidate has capital wealth.
- Stores `present_count`, `nominal_count`, `coverage_value`, and evidence JSON for every score row.

Main limitations of the current implementation:

- `keywords.weight` exists but is **not used** in scoring.
- A single bill can contribute multiple keyword rows, which can overcount one law.
- `self_interest_value` is binary and does not use the candidate's specific wealth composition.
- Coverage is stored, but not elevated into a first-class confidence signal.
- Context laws and core wealth-tax laws are not yet separated strongly enough in the rollup.

---

## Tracker

### 1. Apply keyword weight in scoring

- **Why:** the schema already stores `keywords.weight`, but `score_keyword()` currently ignores it.
- **Current state:** completed; `score_keyword()` now applies `weight` to directional score values.
- **Target:** `score_value = sign * direction * weight`.
- **Files:** `app/score_candidate.py`
- **Status:** completed
- **Notes:** missing weights default to `1.0`; `self_interest_value` uses the weighted score because it is derived from `score_value`.

### 2. Separate core, supporting, and context laws

- **Why:** IGF / offshore / dividends / minimum-tax votes should count more than broad or weak proxies.
- **Current state:** completed; the seed now uses explicit weight tiers for very-high-impact, high-impact, and context-only keywords.
- **Target:** define a stronger curation rule:
  - core = direct taxation of large fortunes, offshore wealth, exclusive funds, dividends, high incomes
  - supporting = adjacent but still distributionally relevant
  - context = explanatory only, low-weight or non-directional
- **Files:** `app/db.py`, follow-up read-model changes if needed
- **Status:** completed
- **Notes:** this is encoded through `weight`: IGF, offshore, exclusive funds, and the high-income minimum tax use very-high weight; dividends use high weight; consumption-tax reform remains low-weight and non-directional context.

### 3. Turn coverage into a visible confidence signal

- **Why:** a politician with 1 covered signature vote should not look as certain as one with 6 or 8.
- **Current state:** completed; the summary now reports weighted confidence beside raw law coverage.
- **Target:** expose:
  - thematic score
  - coverage / share of available weighted laws
  - confidence label or percentage
- **Files:** `app/db.py`, `shared/scorecard.js`, `shared/theme.css`
- **Status:** completed
- **Notes:** `confidence_pct` is weighted coverage over wealth-relevant directional laws. The UI shows it as “confiança da leitura” with an explainer tooltip; raw `coverage_pct` remains for compatibility.

### 4. Separate vote direction from asset-exposure context

- **Why:** a pro-redistribution vote and the candidate's declared exposure to the affected asset class are related but not identical concepts.
- **Current state:** completed; the summary now reports separate weighted vote-direction and asset-exposure context fields.
- **Target:** report two distinct outputs:
  - `pro_redistribution_score`
  - `self_interest_alignment_score`
- **Files:** `app/db.py`, `shared/scorecard.js`, `shared/theme.css`
- **Status:** completed
- **Notes:** `pro_redistribution_score` is the public score: tributação progressiva versus proteção da concentração de riqueza. `self_interest_alignment_score` remains the internal field for asset-overlap context and is only shown when the candidate has relevant declared exposure. Missing votes reduce confidence instead of changing either score.

### 5. Aggregate at the law level before the topic level

- **Why:** one bill with multiple keywords can count multiple times even when it should be one substantive decision with several explanations.
- **Current state:** completed; read-model summaries and `law.score` now use a representative law-level rollup.
- **Target:** compute a representative law-level contribution first, then use keywords as explanatory slices under that law.
- **Files:** `app/score_candidate.py`, `app/db.py`
- **Status:** completed
- **Notes:** keyword scores remain visible for explanation, but summary metrics and the law-level UI score consume one aggregated row per law. A multi-keyword bill now contributes one law weight, not one contribution per keyword.

### 6. Make asset-exposure context asset-specific

- **Why:** the repo already buckets wealth into categories, but the previous context logic only checked whether the candidate had any capital wealth at all.
- **Current state:** completed; `self_interest_value` is now scaled by keyword-specific overlap with declared TSE asset buckets.
- **Target:** scale asset context by the candidate's exposure to the affected asset class:
  - offshore votes weighted more if the candidate has offshore exposure
  - dividend / equity votes weighted more if the candidate holds shares / participations
  - unmatched asset profile -> weak or null asset-overlap signal
- **Files:** `app/score_candidate.py`
- **Status:** completed
- **Notes:** offshore maps to declared foreign deposits; dividends map to shares / participations; exclusive funds map to shares plus fixed-income buckets; IGF only triggers at R$ 10M+ declared wealth; the high-income minimum tax uses capital-income-like buckets as the available proxy.

### 7. Distinguish vote stance from attendance / ambiguity

- **Why:** `Sim`, `Não`, `Abstenção`, `Obstrução`, `AUSENTE`, and `sem votação nominal` are not the same signal.
- **Current state:** completed; the API summary and method text now expose the vote-policy contract.
- **Target:** define an explicit rubric for:
  - directional votes (`Sim` / `Não`)
  - tactical / neutral votes (`Abstenção`, `Obstrução`)
  - missing record (`AUSENTE`, no nominal vote)
- **Files:** `app/score_candidate.py`, possibly read-model summary fields in `app/db.py`
- **Status:** completed
- **Notes:** `Sim`/`Não` affect the progressive-taxation score and the asset-exposure context; `Abstenção`, `Obstrução`, and `Artigo 17` are recorded neutral evidence; `AUSENTE` and `sem votação nominal` reduce coverage/confidence only.

### 8. Curate a signature-vote package per theme

- **Why:** quality of law selection matters more than quantity; the repo's own POC notes already say this explicitly.
- **Current state:** completed for the wealth-tax theme; the package is documented in `research/17-wealth-tax-signature-vote-package.md` and locked by seed tests.
- **Target:** maintain a small, hand-curated package of high-signal wealth-tax votes and document why each vote belongs.
- **Files:** `app/db.py`, `research/17-wealth-tax-signature-vote-package.md`, `tests/test_topic_config.py`
- **Status:** completed
- **Notes:** the current package prioritizes IGF, offshore / exclusive funds, the high-income minimum tax, and dividends; PEC 45 remains context-only.

---

## Suggested implementation order

1. Apply `weight` in `score_keyword()`.
2. Reweight the existing wealth-tax package into core / supporting / context laws.
3. Surface coverage/confidence in the scorecard.
4. Split vote direction and asset-exposure context into separate reported metrics.
5. Add a law-level aggregation rule so one bill does not count multiple times by accident.
6. Upgrade asset-exposure context to use asset-bucket matching.
7. Define the ambiguity/absence policy.
8. Expand and document the signature-vote package.

This order keeps the first improvements small, reversible, and compatible with the existing DB/UI
shape while improving the methodological honesty of the score.

---

## Fit with the current Zucman-inspired wealth-tax theme

With the current repo and current data sources, the best alignment with a Zucman-style framework is:

- give the highest weight to laws directly taxing concentrated wealth
- down-weight broad tax context laws
- show asset-exposure context only when the candidate's asset profile plausibly overlaps the taxed base
- treat the result as a **transparent heuristic**, not a full economic incidence model

That is a stronger and more defensible claim than saying the current code already models wealth
politics in a fully faithful way.
