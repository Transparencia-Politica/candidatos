# Topic → Law Discovery — How to Find the Bills About a Theme

*Compiled 2026-06-26. How to turn a plugged-in topic (e.g. "tributação de riqueza") into the
set of relevant proposições/votações — the standard information-retrieval method, the Brazilian
vocabularies that make it possible, and the pipeline we should build. Theme list and `keywords`
field verified live against the Câmara API.*

> **Why this exists:** the first scorecard discovered votes by `codTema` + recency, which returned
> unvoted 2025 drafts → "0/0 votações" for everyone (a real bug, see §5). The fix is to stop
> guessing and use Brazil's existing **controlled vocabulary** — the bills are already indexed with it.

---

## 1. The answer in one line

**Don't keyword-guess against bill text. Map the topic to controlled-vocabulary *descriptors*
(via the Câmara thesaurus **TECAD**), then match those against each proposição's existing
`keywords`/indexação tags, inside the right `codTema`(s), and keep the ones that were actually voted.**

This is exactly how Congress.gov / Library of Congress do "search legislation by subject."

---

## 2. Is there a consolidated standard list of themes? — Yes, at two levels

### Level 1 — Coarse theme taxonomy (`codTema`): 32 themes
The Câmara's official, closed list (verified live at `/referencias/proposicoes/codTema`):

| cod | tema | cod | tema |
|----|------|----|------|
| 34 | Administração Pública | 57 | Defesa e Segurança |
| 35 | Arte, Cultura e Religião | 58 | Trabalho e Emprego |
| 37 | Comunicações | 60 | Turismo |
| 39 | Esporte e Lazer | 61 | Viação, Transporte e Mobilidade |
| 40 | **Economia** | 62 | Ciência, Tecnologia e Inovação |
| 41 | Cidades e Desenvolvimento Urbano | 64 | Agricultura, Pecuária, Pesca e Extrativismo |
| 42 | Direito Civil e Processual Civil | 66 | Indústria, Comércio e Serviços |
| 43 | Direito Penal e Processual Penal | 67 | Direito e Defesa do Consumidor |
| 44 | Direitos Humanos e Minorias | 68 | Direito Constitucional |
| 46 | Educação | 70 | **Finanças Públicas e Orçamento** |
| 48 | Meio Ambiente e Desenv. Sustentável | 72 | Homenagens e Datas Comemorativas |
| 51 | Estrutura Fundiária | 74 | Política, Partidos e Eleições |
| 52 | Previdência e Assistência Social | 76 | Direito e Justiça |
| 53 | Processo Legislativo e Atuação Parlamentar | 85 | Ciências Exatas e da Terra |
| 54 | Energia, Recursos Hídricos e Minerais | 86 | Ciências Sociais e Humanas |
| 55 | Relações Internacionais e Comércio Exterior | | |
| 56 | Saúde | | |

Get it live: `GET /referencias/proposicoes/codTema`. **Too coarse on its own** — "wealth taxation"
sits inside themes 40 + 70 alongside thousands of unrelated budget/credit items. It's a *filter*,
not the search.

### Level 2 — Controlled vocabulary / thesaurus (the precise instrument)
- **TECAD — Tesauro da Câmara dos Deputados**: ≈ **60,000 terms**, **published in Dados Abertos**.
  Standard thesaurus structure: **descriptors**, **USE / non-descriptors** (synonyms),
  **BT/NT/RT** (broader/narrower/related). It is what indexes every proposição, speech, and law.
  → [TECAD reaches 60k terms](https://www.camara.leg.br/assessoria-de-imprensa/864869-tesauro-da-camara-atinge-a-marca-de-60-mil-termos/) ·
    [TECAD added to Dados Abertos](https://www.camara.leg.br/assessoria-de-imprensa/937793-tesauro-da-camara-e-incluido-no-servico-de-dados-abertos-da-casa/)
- **VCB — Vocabulário Controlado Básico** (Senado / RVBI library network), integrated with
  **LexML** (the national legal-information standard). The Senate analog.
  → [VCB (PDF)](https://www2.senado.leg.br/bdsf/handle/id/532112)

### The crucial fact: bills are already tagged
Each proposição carries its TECAD indexing in the **`keywords`** field. Verified live —
PEC 45/2019 (`/proposicoes/2196833`):
> *"Constituição Federal (1988), alteração, Sistema Tributário Nacional, criação, Imposto sobre
> bens e serviços (IBS), Imposto único, Unificação, IPI, PIS, ICMS …"*

So we **don't** need to invent keyword lists or parse ementa text — the controlled-vocabulary
terms are already on every bill.

---

## 3. How topic → law is usually done (standard practice)

A solved problem in legal information retrieval. Three layers, in order of sophistication:

1. **Controlled-vocabulary indexing.** Indexers (human or ML) assign standardized **subject
   terms** to each bill. Congress.gov uses **CRS Legislative Subject Terms (~1,000)** + a
   **Policy Area** — directly analogous to **TECAD + codTema**.
   → [CRS legislative thesaurus](https://www.ojp.gov/ncjrs/virtual-library/abstracts/legislative-indexing-vocabulary-crs-thesaurus-20th-edition) ·
     [LoC controlled vocabularies](https://www.loc.gov/librarians/controlled-vocabularies/)
2. **Topic → descriptors → query expansion.** Map the topic to its canonical descriptor, then
   walk the thesaurus to pull **synonyms (USE/UF) + narrower (NT) + related (RT)** terms, and
   query the indexed field with that expanded set. The thesaurus turns one fuzzy topic into the
   complete, precise term set. → [Legal information retrieval](https://en.wikipedia.org/wiki/Legal_information_retrieval)
3. **Hybrid semantic search (modern).** Combine **BM25/keyword + thesaurus expansion**
   (precision) with **embeddings** (semantic recall), then rerank. Optional v2.
   → [BM25 + transformer + semantic thesaurus](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9075849/)

---

## 4. Proposed pipeline for our app ("plug a topic")

```
topic  e.g. "tributação de riqueza / renda"
  │
  ├─ 1. THEME FILTER        topic → codTema(s)        → {40 Economia, 70 Finanças}
  │
  ├─ 2. TERM EXPANSION      topic → TECAD descriptors → synonyms (USE/UF) + narrower (NT)
  │        e.g. {Imposto de Renda, dividendos, imposto sobre grandes fortunas, tributação,
  │              fundos, offshore, lucro, IRPF, ITCMD, ...}
  │
  ├─ 3. MATCH BILLS         proposição.keywords (indexação) ∩ expanded-terms   [+ ementa fallback]
  │        within the codTema filter
  │
  ├─ 4. KEEP THE VOTED ONES /proposicoes/{id}/votacoes → keep votações with a nominal roll-call
  │
  └─ 5. (optional) SEMANTIC RERANK   embeddings of topic vs ementa, to catch mis-tagged bills
```

- Steps 1–4 are **fully data-driven, no hand-written keyword lists** — the term set comes from
  TECAD; the tags come from the bills.
- Step 2 is the piece we still need to wire: load TECAD (it's open data) and expand the topic to
  its descriptor neighborhood. A human picks the *topic*; the thesaurus supplies the *terms*.

---

## 5. Why the first attempt returned "0/0" (the bug this fixes)

The initial scorecard discovered votes via `GET /proposicoes?codTema=70&ordenarPor=id&ordem=DESC`
— the **newest proposições by id**, which are freshly-submitted **2025 drafts that have not been
voted**. Result: zero roll-calls found → "0/0 votações" for *every* deputy (incl. Tabata Amaral,
who has in fact voted on hundreds of bills). The earlier single-candidate demo only worked because
the bills were **hand-picked** (PL 4173, PEC 45…) — i.e. cheating the discovery step. The pipeline
in §4 (indexed terms + voted filter) is the correct, generic replacement.

---

## 6. Open questions to verify before building §4

1. **Does `/proposicoes` accept a `keywords=` search param?** (server-side indexação search) —
   if yes, step 3 is one call; if no, we filter client/ETL-side.
2. **TECAD access format in Dados Abertos** — SKOS/RDF download? an API? a file? This determines
   how we automate step 2 (term expansion).
3. **Voted-bill filtering at scale** — finding *all* tax votações for absence analysis (the user's
   "all the laws she was absent of voting") needs iterating votações over a date window and joining
   to theme; `/votacoes` does **not** accept `codTema` (returns 400) and only links to the
   proposição, so theme must come from the proposição. Plan an ETL pass, not per-request live calls.

## 7. Sources
- Câmara API — `/referencias/proposicoes/codTema`, `/proposicoes/{id}` (`keywords`) — verified live 2026-06-26
- [TECAD 60k terms](https://www.camara.leg.br/assessoria-de-imprensa/864869-tesauro-da-camara-atinge-a-marca-de-60-mil-termos/) ·
  [TECAD in Dados Abertos](https://www.camara.leg.br/assessoria-de-imprensa/937793-tesauro-da-camara-e-incluido-no-servico-de-dados-abertos-da-casa/)
- [Senado VCB](https://www2.senado.leg.br/bdsf/handle/id/532112) · LexML
- [Congress.gov CRS subject terms](https://www.ojp.gov/ncjrs/virtual-library/abstracts/legislative-indexing-vocabulary-crs-thesaurus-20th-edition) ·
  [LoC controlled vocabularies](https://www.loc.gov/librarians/controlled-vocabularies/) ·
  [Legal IR (Wikipedia)](https://en.wikipedia.org/wiki/Legal_information_retrieval) ·
  [BM25+transformer+thesaurus](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9075849/)
