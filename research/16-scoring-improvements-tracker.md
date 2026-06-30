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

For the wealth-tax theme, the score should answer two related but different questions:

- Did this politician vote in favor of taxing concentrated wealth?
- When this politician has personal exposure to that kind of wealth, did the vote also protect
  their own financial interest?

Those two questions should stay separate. A redistribution score is about the public policy
direction of the vote. A self-interest score is about whether the candidate's declared assets make
that vote personally relevant. Combining them too early makes the result harder to defend.

The better model with today's tools is:

```text
law_score = vote_sign * direction * weight

topic_score = sum(weighted law scores with recorded votes)
              / sum(weights for covered laws)

confidence = covered_weight / total_possible_weight

self_interest_alignment = law_score * exposure_to_affected_asset_class
```

In plain terms: first decide whether the law really moves policy toward taxing wealth. Then decide
how important that law is for the theme. Then check how the politician voted. Finally, only make a
self-interest claim when the politician's declared assets overlap with the taxed base.

For a Zucman-inspired wealth-tax rubric, that means:

- IGF / large-fortune taxation should carry very high weight.
- Offshore wealth and exclusive-fund taxation should carry very high weight.
- Dividends, capital income, and minimum taxes on very high incomes should carry high weight.
- Broad consumption-tax reform should be context, not strong evidence about wealth taxation.
- Missing votes should reduce confidence, not silently become a political position.

The honest public claim is therefore: the current law package and directions are broadly compatible
with a Zucman-style view of wealth concentration, but the implementation is still a first-pass
heuristic. To make the score stronger, the code needs to use `weight`, aggregate by law, expose
confidence, and scale self-interest by asset exposure.

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
- **Current state:** the seed distinguishes `wealth_relevant` and one context keyword with `direction = 0`, but the rollup does not yet impose a clear tiering model.
- **Target:** define a stronger curation rule:
  - core = direct taxation of large fortunes, offshore wealth, exclusive funds, dividends, high incomes
  - supporting = adjacent but still distributionally relevant
  - context = explanatory only, low-weight or non-directional
- **Files:** `app/db.py`, follow-up read-model changes if needed
- **Status:** pending
- **Notes:** this can be encoded either through `weight` alone or through an explicit tier field later. With today's schema, `weight` is enough.

### 3. Turn coverage into a visible confidence signal

- **Why:** a politician with 1 covered signature vote should not look as certain as one with 6 or 8.
- **Current state:** `present_count`, `nominal_count`, and `coverage_value` are stored, but the thematic score is not explicitly paired with a confidence measure.
- **Target:** expose:
  - thematic score
  - coverage / share of available weighted laws
  - confidence label or percentage
- **Files:** `app/db.py`, `shared/scorecard.js`, `shared/theme.css`
- **Status:** pending
- **Notes:** this is methodologically important because absence and sparse evidence are central limitations in the current POC.

### 4. Separate redistribution score from self-interest score

- **Why:** a pro-redistribution vote and a vote against one's own financial interest are related but not identical concepts.
- **Current state:** both ideas are derived from the same per-keyword sign flip.
- **Target:** report two distinct outputs:
  - `pro_redistribution_score`
  - `self_interest_alignment_score`
- **Files:** `app/db.py`, `shared/scorecard.js`, `shared/theme.css`
- **Status:** pending
- **Notes:** this will make the scorecard easier to defend publicly because it avoids collapsing two claims into one number.

### 5. Aggregate at the law level before the topic level

- **Why:** one bill with multiple keywords can count multiple times even when it should be one substantive decision with several explanations.
- **Current state:** scores are stored per keyword; the read model then rolls them up.
- **Target:** compute a representative law-level contribution first, then use keywords as explanatory slices under that law.
- **Files:** `app/score_candidate.py`, `app/db.py`
- **Status:** pending
- **Notes:** this can still preserve the current UI shape; the change is mostly in the aggregation rule.

### 6. Make self-interest alignment asset-specific

- **Why:** the repo already buckets wealth into categories, but the current self-interest logic only checks whether the candidate has any capital wealth at all.
- **Current state:** `self_interest_value = -score_value` when `wealth_relevant` and `wealth_capital > 0`.
- **Target:** scale self-interest by the candidate's exposure to the affected asset class:
  - offshore votes weighted more if the candidate has offshore exposure
  - dividend / equity votes weighted more if the candidate holds shares / participations
  - unmatched asset profile -> weak or null self-interest signal
- **Files:** `app/score_candidate.py`
- **Status:** pending
- **Notes:** this is the most important step if we want a stronger “voting for the public vs voting for own pocket” claim without inventing new external data.

### 7. Distinguish vote stance from attendance / ambiguity

- **Why:** `Sim`, `Não`, `Abstenção`, `Obstrução`, `AUSENTE`, and `sem votação nominal` are not the same signal.
- **Current state:** the code already distinguishes these statuses, but the rollup still needs a cleaner policy for how each affects the final score.
- **Target:** define an explicit rubric for:
  - directional votes (`Sim` / `Não`)
  - tactical / neutral votes (`Abstenção`, `Obstrução`)
  - missing record (`AUSENTE`, no nominal vote)
- **Files:** `app/score_candidate.py`, possibly read-model summary fields in `app/db.py`
- **Status:** pending
- **Notes:** absence should remain visible as its own signal, not quietly collapse into the same meaning as an anti-redistribution vote.

### 8. Curate a signature-vote package per theme

- **Why:** quality of law selection matters more than quantity; the repo's own POC notes already say this explicitly.
- **Current state:** the seeded package is promising but still small and partly mixed in signal strength.
- **Target:** maintain a small, hand-curated package of high-signal wealth-tax votes and document why each vote belongs.
- **Files:** `app/db.py`, `research/07-poc-candidate-scoring-bivar.md`, future theme-specific research notes
- **Status:** pending
- **Notes:** for the current wealth-tax topic, this should prioritize IGF, offshore / exclusive funds, dividends, and minimum tax on high incomes.

---

## Suggested implementation order

1. Apply `weight` in `score_keyword()`.
2. Reweight the existing wealth-tax package into core / supporting / context laws.
3. Surface coverage/confidence in the scorecard.
4. Split redistribution and self-interest into separate reported metrics.
5. Add a law-level aggregation rule so one bill does not count multiple times by accident.
6. Upgrade self-interest scoring to use asset-bucket matching.
7. Define the ambiguity/absence policy.
8. Expand and document the signature-vote package.

This order keeps the first improvements small, reversible, and compatible with the existing DB/UI
shape while improving the methodological honesty of the score.

---

## Fit with the current Zucman-inspired wealth-tax theme

With the current repo and current data sources, the best alignment with a Zucman-style framework is:

- give the highest weight to laws directly taxing concentrated wealth
- down-weight broad tax context laws
- match self-interest only when the candidate's asset profile plausibly overlaps the taxed base
- treat the result as a **transparent heuristic**, not a full economic incidence model

That is a stronger and more defensible claim than saying the current code already models wealth
politics in a fully faithful way.
