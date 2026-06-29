*Bulk roster scan: enumerate the whole sitting Congress and score every member from the cached
laws — the batch counterpart to on-demand scoring. Compiled & verified live `2026-06-29`.*

# 15 — Bulk roster scan (every deputy + senator)

Until now scoring was strictly **on-demand, one politician at a time** (a UI search → score → the
person joins the roster grid). [`app/scan_all.py`](../app/scan_all.py) adds the batch path: walk
the two official rosters and run the *same* per-politician scoring for the whole house, so every
result is byte-identical to scoring that person by hand.

It is a **crossing** job, not a download job: the laws and their roll-calls are already cached
(a "topic package", research/12) — the scan only matches each politician onto that cache.

## What we need from each roster entry (the join keys)

The single most important fact: **the vote crossing needs only one identifier per politician, and
the roster list already carries it.** No per-politician profile fetch is needed for the votes — it
is a pure DB lookup against the cached `votes` table.

| House | Roster source | Join key (in the list payload) | Crosses against |
|---|---|---|---|
| Câmara | `GET /deputados` (**paginated**) | `id` → stored as `votes.deputy_id` (= `deputado_.id`) | cached `roll_calls`/`votes` where `house='camara'` |
| Senado | `GET /senador/lista/atual` (single list, 81) | `CodigoParlamentar` → `votes.deputy_id`, `house='senado'` | cached `roll_calls`/`votes` where `house='senado'` |

`infer_law_vote_from_cache(conn, <join key>, law, house=…)` does the crossing with **zero** API
calls. The only per-politician *external* cost is the **TSE wealth** lookup (declared assets), which
is the slow, failure-prone leg — not the vote score.

The Câmara list entry also carries `siglaUf`; we pass it straight as the TSE UF so scoring skips
UF inference. Fields verified live `2026-06-29`:
```jsonc
// GET /deputados?ordem=ASC&ordenarPor=nome&itens=5&pagina=1  → dados[0]
{ "id": 204379, "nome": "Acácio Favacho", "siglaPartido": "MDB", "siglaUf": "AP", "idLegislatura": 57 }
```

## Pagination (the "N pages" knob)

`/deputados` pages with `pagina` + `itens`, and every page carries `links[]` with `rel:self|next|
first|last`. **Follow `rel:next` until it is absent** — that is the stop condition (don't trust a
fixed count). Verified live: with `itens=5`, `rel:last` resolved to `pagina=103` (≈513 deputies).

```text
itens=5,  pagina=1 → rel:next = …pagina=2…   rel:last = …pagina=103…
```

`scan_all.iter_deputies(pages, itens)` is pure HTTP (no DB), so the pager is smoke-tested in
isolation. **First goal = `--pages 1`** (one small page) before any full run. `--pages 0` = all
pages. `/senador/lista/atual` is **not** paginated — it returns all 81 at once.

## Budget discipline (verified)

The user constraint was "download all of them with the waiting times so we don't blow up our
budget." Two structural costs were removed so a full run is affordable, plus pacing knobs:

1. **TSE `listar` memoization** — `score_candidate._tse_listar(year, uf, eid, cargo)` is
   `@lru_cache`d. The TSE candidate list is ≈150 rows **per UF** (AP/cargo 6 = 154 rows, verified
   live) and was previously refetched for *every* candidate. Memoized, a full run costs ≈27 listar
   calls (one per UF) instead of ≈513. A 2022 candidacy roster is immutable, so the cache never
   goes stale; exceptions are not cached, so a transient TSE failure is retried. Cargo 6 (deputy
   match) and cargo 5 (senator-wealth match) share the same memo. ✅ verified: a repeat lookup is a
   cache hit, 1 network call for 2 lookups.
2. **Senado package built once** — `senado.score_senator(..., build_package=False)` skips the heavy
   per-law Senado roll-call ingest. `scan_senators` builds the package **once**, then scores all 81
   from cache. Before this, a naïve senator loop re-ingested every law's Senado votações **81
   times** — the biggest budget leak, and the senator-side twin of the listar problem. The default
   (`build_package=True`) keeps the single-senator UI path (`server.py`) byte-identical.
3. **Pacing** — `--pause` spaces calls *inside* one scoring run; `--candidate-pause` spaces
   consecutive politicians. Per-politician errors (unresolved TSE match, deleted profile) are caught
   and logged so one failure never aborts the batch.

## Prerequisite & gotcha

The scan **crosses against** the vote cache; it does not build it. If the Câmara cache is empty,
every deputy silently scores `AUSENTE` and the run *looks* broken. `scan_deputies` therefore guards
with `SELECT COUNT(*) FROM roll_calls WHERE house='camara'` and warns loudly at 0. Building the
cache is opt-in (`--ingest-cache`, or `ingest.ingest_all` by hand) — never automatic, because it is
heavy and contradicts the "N=1 first" goal. The Senado cache *is* built (once) by the senator scan.

## Usage

```bash
# smallest real smoke test — page 1, 5 deputies (matches the "N=1 pages" first goal)
python app/scan_all.py --pages 1 --itens 5

# a UF-batched chunk of deputies
python app/scan_all.py --pages 5 --itens 50

# the whole Congress (all deputy pages + all 81 senators)
python app/scan_all.py --pages 0 --senators

# build the Câmara vote cache first, then scan
python app/scan_all.py --ingest-cache --pages 1
```

Requires the Docker MySQL up (`docker compose up -d mysql`) and the laws seeded/ingested.
