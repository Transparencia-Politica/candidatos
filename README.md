# candidatos — Candidato (Transparência-Política) (research & data layer)

A Brazilian analog of Germany's [Wahl-O-Mat](https://www.wahl-o-mat.de/), targeting the
**2026 Brazilian general election** (1st round **4 Oct 2026**). The distinguishing idea: instead
of matching voters to *self-reported* party answers, ground each thesis in **real legislative
behavior** — how parties/candidates actually voted, attended, authored, and were financed.

This repo currently holds the **research and data-access groundwork** (no app code yet).

## Document map

### Root
| File | What it is |
|---|---|
| [`DATA-SOURCES.md`](DATA-SOURCES.md) | Master list of every data source (Câmara, Senado, TSE, Base dos Dados, civic-tech) with links + a signal→source pipeline mapping. Start here. |
| [`REPO-ANALYSIS.md`](REPO-ANALYSIS.md) | Full technical reports on two reference MCP servers (`brazil-mcp-server`, `brazilinfo-mcp`). Architecture references only — neither has electoral data. |
| [`wahl-o-mat-methodology.md`](wahl-o-mat-methodology.md) | Canonical Wahl-O-Mat methodology + matching math + **glossary** (Trennschärfe etc.) + Brazil adaptation notes. |

### `research/`
| File | What it is |
|---|---|
| [`01-camara-senado-apis.md`](research/01-camara-senado-apis.md) | Verified Câmara & Senado open-data endpoints: votes, attendance, authorship, expenses, tema taxonomy. |
| [`02-tse-candidate-data.md`](research/02-tse-candidate-data.md) | TSE bulk + DivulgaCandContas API: candidates, assets, finance, ficha-limpa; Base dos Dados; 2026 timeline. |
| [`04-matching-pipeline-design.md`](research/04-matching-pipeline-design.md) | Brazilian prior art (brasil.vota.com, Radar Parlamentar, Basômetro, Ranking dos Políticos, Serenata) + scoring design + VAA pitfalls. |
| [`05-questao-publica-2010-first-brazilian-VAA.md`](research/05-questao-publica-2010-first-brazilian-VAA.md) | The first Latin-American VAA (2010 Senate). Includes the full **35-statement Portuguese thesis bank** + lessons. |
| [`06-vaa-academic-literature.md`](research/06-vaa-academic-literature.md) | Synthesis of 4 peer-reviewed VAA papers → concrete design directives. |
| [`07-poc-candidate-scoring-bivar.md`](research/07-poc-candidate-scoring-bivar.md) | Live POC: joined TSE wealth ⨯ Câmara tax votes for one deputy. Verdict + reproducible calls. |
| [`08-api-field-notes.md`](research/08-api-field-notes.md) | Hard-won API gotchas (DivulgaCand route shape, Câmara `/votos`, zsh, rate limits). Read before coding ingestion. |

### `app/` and `docs/`
| File | What it is |
|---|---|
| [`app/db.py`](app/db.py) | Local MySQL schema and read model for `topics -> laws -> keywords -> scores <- politics`. |
| [`app/score_candidate.py`](app/score_candidate.py) | One-candidate scoring script that fetches official APIs and stores calculated scores. |
| [`app/server.py`](app/server.py) | Local HTTP server with `/api/scorecards`, `/api/politics`, and `/api/topics`. |
| [`app/index.html`](app/index.html) | Static frontend consuming the local scorecard API. |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Implementation note for the database model and runtime flow. |

Local app/database environment:

```bash
docker compose up --build
docker compose run --rm app python app/score_candidate.py
```

The two reference MCP repos analyzed in `REPO-ANALYSIS.md` are **not bundled** here — clone them
from their GitHub URLs (listed in that doc) if you want to read their source.

## Key decisions so far (rationale in the docs above)

1. **Behavioral data over self-report.** Derive incumbent positions from roll-call votes; reserve
   self-report for non-incumbent challengers and label it. *Why:* self-report is sparse and gamed
   — empirically the strongest candidates opt out (Questão Pública 2010; doc 05) and self-place
   strategically (doc 06).
2. **Ranked list, never a single "best match."** *Why:* the matching method changes the top match
   for up to ~90% of users (Louwerse & Rosema; doc 06).
3. **High-dimensional matching** (agreement / city-block over raw theses); treat any 1D/2D
   ideological map as a separately-validated secondary view. *Why:* low-dim projections distort
   toward fringe parties (doc 06).
4. **Depth over breadth** — several theses per Brazilian cleavage. *Why:* accuracy rises with
   questions-per-area; secondary issues barely discriminate with few items (doc 06).
5. **Behavioral *Trennschärfe* as the thesis filter** — keep theses whose underlying votes
   actually split the houses (the empirical version of Wahl-O-Mat's "only divisive statements
   survive" rule; `wahl-o-mat-methodology.md` + doc 06).
6. **Transparent math, no neutrality claims; every thesis links to its evidence** (the bill/vote).
   *Why:* VAA design is never neutral (Fossen & Anderson; doc 06).

## Open next steps

- Turn the research into a single **design spec** (thesis schema, matching engine, ingestion plan).
- Scale the POC (doc 07) to a **batch run over all ~513 deputies on 5–8 hand-coded signature
  votes**, with `/orientacoes` for direction and attendance modeled explicitly.
- Decide the **steward/governance model** (independent, non-partisan — the bpb/Questão Pública pattern).

## Non-partisan disclaimer

This is a **non-partisan civic-tech research project**. It does not endorse, oppose, or rank any
party or candidate. Where individual politicians are named (e.g. the POC in `research/07`), the
analysis is **illustrative**, drawn entirely from **official public records**, and explicitly
caveated (e.g. a missed vote is reported as "no recorded vote", never as intent). Findings about
single individuals are anecdotes (n=1), not conclusions. The goal is to help voters compare
positions against evidence — not to tell anyone how to vote.

## Data sources & attribution

All data comes from official open-data portals; respect each provider's terms:

- **Câmara dos Deputados** — Dados Abertos (`dadosabertos.camara.leg.br`)
- **Senado Federal** — Dados Abertos (`legis.senado.leg.br/dadosabertos`)
- **TSE** — Dados Abertos + DivulgaCandContas (`dadosabertos.tse.jus.br`)
- **Base dos Dados** (`basedosdados.org`) — CC BY licensing on its curated tables

Third-party tools/papers referenced in `research/` belong to their respective authors and are
cited, not redistributed. Academic PDFs are referenced by DOI only.

## License

> **TODO (repo owner):** add a `LICENSE` file. Suggested: docs/text under **CC BY 4.0**, any
> code under **MIT**. Not set yet — choose before publishing.
