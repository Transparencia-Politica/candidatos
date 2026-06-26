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

**Current stage: research & data-access groundwork. There is no app code yet.** The deliverables
here are documents: verified data-source maps, API field notes, methodology, and a scoring POC.
**Treat the docs as the product.**

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

## Working norms

- **Answer questions as questions.** Don't start editing files or running ingestion just because
  a question implies work — act only when asked to.
- **Don't invent data.** Every number, route, or code (idEleicao, cargo, SQ_CANDIDATO…) must
  trace to a primary source or a live call you made.
- Keep the project's stance: **non-partisan, transparent math, every thesis linked to its
  evidence.** No "best match" claims — ranked lists only (see `README.md` decisions).
