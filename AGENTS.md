# AGENTS.md — Candidato (Transparência-Política)

Binding contract for any agent (or human) working in this repository. Read this **before**
touching anything, then use [`INDEX.md`](INDEX.md) to find the right document for your task.

## What this repo is

The **research & data layer** for **Candidato** — the voting-advice application of the
**Transparência-Política** project, targeting the **2026 Brazilian general election**
(1st round **4 October 2026**). The model is Germany's
[Wahl-O-Mat](https://www.wahl-o-mat.de/), but Candidato's distinguishing idea is to back each
thesis with **real legislative behavior** — how parties/candidates actually voted, attended,
authored, and were financed — instead of self-reported manifesto answers.

**Current stage: research & data-access groundwork, plus a working scoring POC** (`app/` —
ingestion, MySQL store, scoring, and a small server) **and a two-front-end scorecard UI**
(see *Frontend: shared UI, two consumers* below). The research deliverables are still the core
product — verified data-source maps, API field notes, methodology — so **treat the docs as the
product**, but the POC app and UI are real code held to the conventions below.

## Layout

| Path | What it holds |
|---|---|
| `README.md` | Narrative overview + key design decisions (with rationale). The human entry point. |
| `INDEX.md` | The document index — file → purpose → when to read, plus reading order by task. |
| `DATA-SOURCES.md` | Master list of every data source (Câmara, Senado, TSE, Base dos Dados, civic-tech). |
| `REPO-ANALYSIS.md` | Technical analysis of the two reference MCP servers. Architecture references only. |
| `wahl-o-mat-methodology.md` | Canonical Wahl-O-Mat methodology, matching math, and glossary. |
| `research/` | Numbered research reports (verified findings). Add new reports here. |
| `docs/` | Working / discovery notes. |

The two third-party MCP repos analysed in `REPO-ANALYSIS.md` are cloned **outside** this repo
(under the parent workspace's `_reference/`) and are read-only references — neither contains
electoral data.

## The rule: document findings while in research mode

This repo runs in **research mode**. The whole point is that hard-won knowledge survives the
session that discovered it. Therefore:

1. **Any non-trivial finding gets written down as you discover it** — a verified API route, a
   gotcha, a data quirk, a methodology decision, even a dead end that wasted time. If you learned
   it the hard way, the next agent shouldn't have to.
2. **Where it goes:**
   - A new, self-contained investigation → a new numbered report in `research/`
     (`NN-short-kebab-title.md`, next number in sequence).
   - An operational gotcha about an existing source/API → append to
     [`research/08-api-field-notes.md`](research/08-api-field-notes.md).
   - A new data source → add a row to [`DATA-SOURCES.md`](DATA-SOURCES.md).
   - A decision that changes direction → update the "Key decisions" list in
     [`README.md`](README.md) with its rationale.
3. **Every factual claim cites its primary source** — link the URL or the exact API call inline,
   and note whether it was *verified live* and on what date (the existing docs do this; match them).
4. **Update [`INDEX.md`](INDEX.md)** (and `README.md`'s document map) when you add, remove, or
   rename a document — in the same change.
5. **Prefer updating an existing doc over creating a near-duplicate.** Check `INDEX.md` first.

A research session that produced insight but left no document is **incomplete**, even if the
question was answered in chat.

## Documentation conventions (match the existing docs)

- Markdown, opening with a 1–2 line italic header stating what the file is and when it was
  compiled / verified.
- Tables for source lists and route maps; fenced code blocks for example API calls.
- Verified ✅ / failed ❌ markers for anything you actually tested.
- Portuguese terms kept in Portuguese (cargo, tema, ficha-limpa…) with a gloss on first use.
- Convert relative dates to absolute (e.g. "today" → `2026-06-26`).

## Code conventions

- **Code is written in English.** All schema identifiers (table names, columns, indexes,
  constraints), function/variable names, and code in general use English — e.g. `roll_calls`,
  `votes`, `vote_type`, `deputy_id`, not `votacoes`/`votos`/`tipo_voto`.
- **Two exceptions stay in Portuguese:** (a) user-facing strings shown to voters, and (b) the
  external Câmara/TSE API contract — their URL paths (`/votacoes`, `/votos`, `/orientacoes`)
  and JSON field names (`tipoVoto`, `deputado_`, `dados`, `descricao`) are mirrored verbatim,
  never translated.
- Pre-existing Portuguese identifiers from before this rule (e.g. `laws.camara_proposicao_id`)
  are migrated opportunistically, not via unrelated PRs.
- Docs prose follows its own rule (keep domain terms in Portuguese with a gloss — see above);
  this section governs **code only**.

## Frontend: shared UI, two consumers

The scorecard UI is consumed by **two** front ends that must stay visually and behaviorally
consistent. They differ **only** in their data layer and entry UI — never in styling or card
rendering.

- **Live page** — `app/index.html`, served by the **running server** `app/server.py`. Works
  against a live backend (`/api/*`): name search, on-demand scoring, reads from MySQL. The
  server serves shared assets at `/shared/*` straight from the repo-root `shared/` dir.
- **GitHub Pages** — `docs/index.html`, a **static** page with **no backend**. It reads a baked
  **snapshot** (`docs/data/scorecards.json`) and shows the candidates one at a time. Pages only
  serves files under `docs/`, so it loads `docs/shared/` — a **generated copy** of `shared/`.

**The rule: all UI changes go in `shared/`.** `shared/theme.css` (theme, dark/light tokens,
every component, the day/night toggle) and `shared/scorecard.js` (formatters, card-render
helpers, `initThemeToggle`) are the **single source of truth**. Both `index.html` files are
**thin shells** holding only their environment-specific glue (data fetch + entry UI). Do **not**
add styling or card-rendering logic into a shell, and do **not** edit `docs/shared/` directly —
it is regenerated by `python app/snapshot.py site`, which copies `shared/*` into `docs/shared/`.

When you change shared UI, **verify both**: the live page through `app/server.py` (a plain static
file server resolves `shared/` to the wrong path), and the docs page through a static serve of
`docs/`. Run `python app/snapshot.py site` so the committed `docs/shared/` copy stays in sync,
and commit `shared/` and `docs/shared/` together.

## Working norms

- **Answer questions as questions.** Don't start editing files or running ingestion just because
  a question implies work — act only when asked to.
- **Don't invent data.** Every number, route, or code (idEleicao, cargo, SQ_CANDIDATO…) must
  trace to a primary source or a live call you made.
- Keep the project's stance: **non-partisan, transparent math, every thesis linked to its
  evidence.** No "best match" claims — ranked lists only (see `README.md` decisions).
