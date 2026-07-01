# Integration Plan — Porting the Preliminary Engine into Tiago's Backend

*Compiled 2026-06-27. How the live-fetch preliminary implementation (branch `live-engine-poc`)
maps onto Tiago's MySQL/DB backend (`main`), what he already absorbed, the true remaining delta,
and the layer-by-layer port. Grounded in a full read of `app/db.py`, `app/score_candidate.py`,
`app/server.py` and a branch comparison `main` vs `live-engine-poc`.*

> **TL;DR.** Tiago rewrote our preliminary engine as a proper backend and *already carried over
> most of it*. The genuine remaining delta is **3 things**: (1) topic→law **discovery**,
> (2) **Government/Opposition alignment** metric, (3) **mandate-aware presence**. Each must enter
> his **aggregation hierarchy** at the right layer (capture → aggregate → render), not be bolted on.

---

## 1. How Tiago's backend works (architecture + data aggregation)

It is a **generalized, hierarchical VAA rollup** — not just "store scores".

### Schema (`db.py`, MySQL + SQLite fallback)
```
topics ─< laws ─< keywords ─< scores (politic × keyword) >─ politics
```
- `topics(slug,title,description,sort_order)`
- `laws(topic_id, camara_proposicao_id*, label, kind, number, year, description, source_url, is_key, wealth_relevant, sort_order)`
- `keywords(law_id, slug, label, description, direction ±1/0, weight, wealth_relevant, sort_order)`
- `politics(camara_id, tse_sq, name, party, uf, wealth_total, wealth_capital, wealth_buckets, profile…)`
- `scores(politic_id, keyword_id, score_value, self_interest_value, vote_status, vote_label, stance, present_count, nominal_count, coverage_value, evidence JSON)`

### Scoring flow (`score_candidate.py::score_camara_candidate`)
1. Câmara profile → UF → `resolve_tse_candidate` (name match) → `bens` → `bucketize_assets` → `wealth_capital` (ações + exterior).
2. `db.upsert_politic(...)`.
3. For each law in **`db.list_laws_with_keywords`** (the *seeded* set, currently 3):
   - `infer_law_vote()` — fetch law `/votacoes` (newest `limit_votes`=25), per votação `/votos`, find deputy, count `present/nominal`, derive `stance` (passage if "aprovad" in desc, else single distinct vote).
   - `score_keyword()` — `score = vote_sign(stance) × keyword.direction`; `self_interest = −score` when `wealth_relevant & wealth_capital>0 & direction≠0`.
   - `db.upsert_score(...)` with `evidence`.

### Data aggregation (the part that matters for integration)
The read model `get_scorecard_for_politic` returns `{ politic, summary, topics }`:
- **`_topics_for_politic`** — one JOIN rebuilds the **topic → law → keyword → score tree** (nested for the UI). Each law carries a representative score; each keyword its own.
- **`_summary`** — rolls up to the politician (**dedup per law**):
  - `wealth_capital_pct`
  - `coverage_pct` = recorded / **wealth-relevant** laws
  - `key_attendance_pct` = present/nominal on the **`is_key`** law
  - **`self_interest_alignment_pct`** = share of wealth-relevant votes that *protect* own wealth (`self_interest_value > 0`)
  - counts: `self_interest_n`, `relevant_laws_n`, `recorded_laws_n`

### Serving (`server.py`)
REST over the DB: `GET /api/candidates/search`, `GET /api/topics`, `POST /api/scorecards` (calc+cache), `GET /api/scorecards/{camara_id}` (read). `index.html` renders the topics-tree + summary from the API. No browser→Câmara/TSE calls.

**Two design facts I initially under-weighted:**
1. **It's multi-topic** — a general VAA skeleton, not wealth-tax-only (our prelim was single-topic, flat).
2. **He already ported our asset-exposure metric** into `_summary` (`self_interest_alignment_pct`) — so it is **not** a delta.

---

## 2. What he already absorbed from our prelim (NOT deltas)
- Wealth `bucketize_assets` (= our `bucketize`); `wealth_capital` = ações + exterior
- TSE resolution by name match → `bens`
- Câmara `/votos`, `present/nominal/stance` (`vote_class`)
- **asset-exposure context = −score** for wealth-relevant keywords (now `self_interest_alignment_pct`)
- Server-side fetch with **retry** (429/5xx); **DB caching** of scorecards
- Deputy search

---

## 3. The true remaining delta (ours, not yet in his)

Confirmed by branch comparison (`live-engine-poc` markers absent from `main`):

| # | Feature | His state | Port target |
|---|---|---|---|
| 1 | **Topic→law discovery** (`buildUniverse` + TECAD `DESCRIPTORS`) | hand-seeds **3 laws** | new `app/discover_laws.py` + `db.upsert_law/upsert_keyword` |
| 2 | **Government/Opposition alignment %** (from `/orientacoes`) | absent | `infer_law_vote` + `_summary` + frontend |
| 3 | **Mandate-aware presence** (current-legislature scoping) | samples newest 25 regardless of term | filter inside `infer_law_vote` |

*(Freebie: `keyword.weight` exists but is unused — descriptor weighting drops in once discovery feeds it. `laws.description` exists — readable law names are a render concern, populated by discovery.)*

---

## 4. Layer-by-layer integration map

Each feature must enter at the right layer of his pipeline:

| Feature | Capture (fetch) | Aggregate (`_summary`) | Render (`index.html`) |
|---|---|---|---|
| **Discovery** | `discover_laws.py` writes `laws`+`keywords` (full topic→law→keyword tree: `direction`, `weight`, `is_key`, `wealth_relevant`, `sort_order`) | — (scoring then iterates them automatically) | optional explorer page (our `discover.html`, server-side variant) |
| **Gov/Opp alignment** | add `/votacoes/{id}/orientacoes` to `infer_law_vote`; stash in `evidence` | **add `gov_alignment_pct`** | add a pill |
| **Mandate scoping** | term-window filter on `votacoes` in `infer_law_vote` | feeds existing `coverage_pct` / `key_attendance_pct` | — |

**Key constraint:** discovery must **emit his data shape** (topic→law→keyword with directions), not a flat bill list — otherwise it won't flow through `_summary`.

---

## 5. The one open design question: `keyword.direction` for discovered laws
Discovery finds *which* bills are on-topic; "does `Sim` advance the thesis?" still needs a value:
- **a)** default `+1` + human review,
- **b)** derive from `/orientacoes` (Governo line) — ties #2 into #1,
- **c)** one-off LLM pass over the ementa (acceptable as an offline seeding step, unlike in the live page).

This choice decides fully-automatic vs. semi-curated discovery.

---

## 6. Git workflow (so nothing lands on `main` unreviewed)
- Base = `main` (Tiago's). Reference = `live-engine-poc` (our prelim; `git diff main live-engine-poc -- app/index.html` is the port spec).
- One improvement per branch off `main`:
  - `feat/law-discovery` → `discover_laws.py` + `db.upsert_law/keyword` (do first — biggest value; raises the direction question)
  - `feat/orientacao-direction` → orientação in `infer_law_vote` + `gov_alignment_pct` in `_summary` (answers the direction question from data)
  - `feat/mandate-presence` → term-window filter
- Test each on the **SQLite path** (no Docker): `DATABASE_URL=sqlite:///./x.sqlite python app/score_candidate.py --seed-only` → `--camara-id <id>` → start `server.py` → check `/api/scorecards/{id}`.

## 7. Status
- Merge to Tiago's base: **done** (`e50bafc`), verified end-to-end on SQLite.
- Our prelim preserved on branch **`live-engine-poc`**.
- Next: `feat/law-discovery` (pending direction-question decision §5).
