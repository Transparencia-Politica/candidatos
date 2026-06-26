# INDEX — Candidato (Transparência-Política)

*The document index for this research repo. Find the right file by task, then read it.
For the narrative overview and the design decisions, start at [`README.md`](README.md);
for the working contract (including the rule to document findings), read
[`AGENTS.md`](AGENTS.md).*

This repo is the **research & data layer** for **Candidato**, the voting-advice application of
the **Transparência-Política** project. There is no app code yet — the documents are the product.

## How to use this folder

1. **New here?** Read [`README.md`](README.md) (overview + key decisions), then this index.
2. **Working on a task?** Jump to the matching file via the tables below.
3. **Found something non-trivial?** Write it down — see *Documenting findings* at the bottom.

## All documents

### Root

| File | What it is | Read it when… |
|---|---|---|
| [`README.md`](README.md) | Narrative overview + key design decisions (with rationale). | You need the big picture or the "why" behind a decision. |
| [`AGENTS.md`](AGENTS.md) | Working contract: layout, conventions, the document-findings rule. | Before doing any work here. |
| [`DATA-SOURCES.md`](DATA-SOURCES.md) | Master list of every data source (Câmara, Senado, TSE, Base dos Dados, civic-tech) + signal→source mapping. | You need to know *where* a piece of data comes from. |
| [`wahl-o-mat-methodology.md`](wahl-o-mat-methodology.md) | Canonical Wahl-O-Mat methodology, matching math, and glossary (Trennschärfe etc.) + Brazil adaptation notes. | You're designing theses or the matching engine. |
| [`REPO-ANALYSIS.md`](REPO-ANALYSIS.md) | Technical analysis of the two reference MCP servers. Architecture references only — neither has electoral data. | You want prior art for an MCP/data-server architecture. |

### `research/`

| File | What it is | Read it when… |
|---|---|---|
| [`01-camara-senado-apis.md`](research/01-camara-senado-apis.md) | Verified Câmara & Senado open-data endpoints: votes, attendance, authorship, expenses, tema taxonomy. | Ingesting legislative behavior. |
| [`02-tse-candidate-data.md`](research/02-tse-candidate-data.md) | TSE bulk + DivulgaCandContas API: candidates, assets, finance, ficha-limpa; Base dos Dados; 2026 timeline. | Ingesting candidate / electoral data. |
| [`04-matching-pipeline-design.md`](research/04-matching-pipeline-design.md) | Brazilian prior art + scoring design + VAA pitfalls. | Designing the matching pipeline. |
| [`05-questao-publica-2010-first-brazilian-VAA.md`](research/05-questao-publica-2010-first-brazilian-VAA.md) | The first Latin-American VAA (2010 Senate) + full 35-statement Portuguese thesis bank + lessons. | Writing the thesis bank; learning from prior failures. |
| [`06-vaa-academic-literature.md`](research/06-vaa-academic-literature.md) | Synthesis of 4 peer-reviewed VAA papers → concrete design directives. | Justifying a methodology choice. |
| [`07-poc-candidate-scoring-bivar.md`](research/07-poc-candidate-scoring-bivar.md) | Live POC: TSE wealth ⨯ Câmara tax votes for one deputy. Verdict + reproducible calls. | Scaling the scoring approach. |
| [`08-api-field-notes.md`](research/08-api-field-notes.md) | Hard-won API gotchas (DivulgaCand route shape, Câmara `/votos`, rate limits). | **Before coding any ingestion.** |

### `docs/`

| File | What it is |
|---|---|
| [`docs/DISCOVERY.md`](docs/DISCOVERY.md) | Seed reference + pointer into the research corpus. |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Local MySQL schema, Docker Compose setup, and scorecard runtime flow. |

### `app/`

| File | What it is |
|---|---|
| [`app/db.py`](app/db.py) | MySQL schema, seed data, and scorecard read model. |
| [`app/score_candidate.py`](app/score_candidate.py) | One-candidate ingestion/scoring script for Câmara + TSE data. |
| [`app/server.py`](app/server.py) | Local HTTP server exposing scorecard APIs and serving the frontend. |
| [`app/index.html`](app/index.html) | Frontend that consumes `/api/scorecards`. |

## Reading order by task

- **Understand the project** → `README.md` → this index → `wahl-o-mat-methodology.md`.
- **Build data ingestion** → `DATA-SOURCES.md` → `01` / `02` → `08-api-field-notes.md` (read last, it's the gotchas).
- **Design the matching engine** → `wahl-o-mat-methodology.md` → `04` → `06`.
- **Write the thesis bank** → `05` → `06` → `wahl-o-mat-methodology.md`.
- **Scale the scoring POC** → `07` → `01` / `02`.
- **Work on the local scorecard DB/API** → `docs/DATABASE.md` → `app/db.py` →
  `app/score_candidate.py` → `app/server.py`.

## Documenting findings (research mode)

This repo runs in research mode: **write down any non-trivial finding as you discover it.**
New investigation → a numbered `research/NN-*.md`; an API gotcha → append to `08`; a new source →
a row in `DATA-SOURCES.md`; a direction-changing decision → `README.md`. Cite every claim's
primary source and note whether it was verified live and when. **Update this index in the same
change.** Full rule in [`AGENTS.md`](AGENTS.md).
