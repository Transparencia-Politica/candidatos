*Verified live 2026-06-27. How we cross our seeded laws with **Senado** (Senate) nominal
roll-calls so senators score against the same law package as deputies — and the API contract,
gotchas, and honest coverage limits. Builds on the vote-cache design in
[`12-topic-packages-and-vote-caching.md`](12-topic-packages-and-vote-caching.md).*

## 1. The idea: the law is the join point

A federal bill is voted in **both** houses. So the same `laws` row gathers Câmara *and* Senado
roll-calls — we find a law's Senado twin by the `kind`/`number`/`year` we already store
(e.g. `PEC`/`45`/`2019`) and hang the Senado roll-calls off the **same `law_id`**. Adding the
Senado is therefore a *second voter population on the laws we already have*, not new laws. The
vote-cache argument from `12` carries over unchanged: a Senado roll-call is immutable and
voter-independent, so fetch once, look up forever.

## 2. Verified Senado open-data API (host `legis.senado.leg.br/dadosabertos`)

All return JSON when sent `Accept: application/json` (despite XSD references in the payload).

| Need | Route | Returns |
|---|---|---|
| Current senators | `/senador/lista/atual` | ✅ `ListaParlamentarEmExercicio.Parlamentares.Parlamentar[]`, each `IdentificacaoParlamentar.{CodigoParlamentar, NomeParlamentar, NomeCompletoParlamentar, SiglaPartidoParlamentar, UfParlamentar}` |
| Bill → matéria code | `/processo?sigla=PEC&numero=45&ano=2019` | ✅ `[{codigoMateria, …}]` — the modern processo service |
| Matéria roll-calls | `/votacao?codigoMateria=158930` | ✅ list of votações; each nominal one carries **every senator's vote inline** in `votos[]` |

One vote row: `{codigoParlamentar, nomeParlamentar, siglaPartidoParlamentar, siglaUFParlamentar, siglaVotoParlamentar}`. `siglaVotoParlamentar` is the vote — **"Sim" / "Não" / "Abstenção"** (same strings as the Câmara), plus absence/leave codes (e.g. `NCom` = não compareceu). A votação object also has `codigoSessaoVotacao` (unique id), `descricaoVotacao`, `dataSessao`, `resultadoVotacao`, `votacaoSecreta` (`N`/`S`).

### Gotchas (verified)
- ❌ **Deprecated endpoints still answer but are dying:** `/materia/votacoes/{cod}` and
  `/materia/pesquisa/lista` carry a `Descontinuacao` notice (full shutdown 2026-02-01) and the
  first returns *no* `Votacoes` node for some matérias. Use `/votacao?codigoMateria=` and
  `/processo?sigla=…` instead. `/processo/{id}` (path form) **404s** — only the query form works.
- ⚠️ **Symbolic votes return `[]`.** `/votacao?codigoMateria=` is empty when the bill passed by
  acclamation — handled as the existing "sem votação nominal" case (no row stored).
- The Senado `/votacao` payload carries **no Governo/Oposição orientation**, so senado roll-calls
  store `gov_orientation = opp_orientation = NULL` and gov-alignment is `None` for senators.
- Only votes in `{Sim, Não, Abstenção, Obstrução}` are stored (PRESENT_VOTES); absence codes are
  skipped so the senator is counted in the nominal denominator but not as present.

## 3. How it lands in the schema (shared, house-tagged)

A `house` column (`'camara'|'senado'`) tags `roll_calls` and `votes`; `politics` gains
`senado_id` + `house` and `camara_id` becomes nullable (senators have no camara id). Senado
roll-call ids are prefixed `sf-<codigoSessaoVotacao>` to stay globally unique.

**The pollution guard (load-bearing):** `get_law_roll_calls` and `get_deputy_votes` default to
`house='camara'`, so the nominal *denominator* for a deputy never includes senado roll-calls —
otherwise every deputy would be marked AUSENTE on senate-only votes. The senator path passes
`house='senado'`. Covered by `tests/test_senado_cross.py`.

## 4. Honest coverage on the current law set (verified 2026-06-27)

Crossing reuses the laws cleanly, but only bills with a **nominal** Senado vote yield a recorded
stance. Of the seeded wealth/tax laws, the wealth-tax bills mostly cleared the Senate
**symbolically**: `PL 4173/2023` (mat. 160970), `PL 1087/2025` (170775), `PL 2337/2021` (149730)
all return `[]`. PECs (constitutionally nominal) and several PLPs do have votes — `PEC 45/2019`
(158930, 5 votações) is the clean end-to-end demo.

⚠️ **Curation caveat — do not blind-trust the cross.** `PLP 108/2024` (166095) has nominal votes,
but they are on the **substitutive / emendas**, *not* the IGF wealth destaque (Emenda de Plenário
nº 8, rejected 262–136 in the Câmara) that the `igf-grandes-fortunas` keyword pins `direction=1`
to. Attaching a senator's "Sim on the substitutive" to a keyword reading "Sim = tax great
fortunes" is a **misattribution**. Each crossed Senado votação needs a curation pass to confirm it
matches its keyword's `direction` before the score is trusted — the wiring is correct, the
per-law semantics are not automatic.

## 4b. Senator wealth (TSE bens) — verified 2026-06-28

Senators carry declared wealth too, pulled with the **same** TSE machinery as deputies
(`bucketize_assets`, `fetch_tse_detail`). The candidate is resolved by **cargo 5 (Senador)**,
matching name+UF:

```
GET .../candidatura/listar/{year}/{uf}/{2040602022}/5/candidatos   # cargo 5 = Senador
GET .../candidatura/buscar/{year}/{uf}/{2040602022}/candidato/{sq} # -> .bens, .totalDeBens
```

- ✅ **2022 general código `2040602022` verified** for cargo 5 (e.g. Alan Rick → R$ 2.12M, 13 bens).
- ❌ **2018 código not resolvable** via this REST API: the elections-list routes 404 and
  `candidatura/listar/2018/.../5/...` returns an empty list for every código tried
  (`2030402018`, …). Senators serve staggered 8-year terms, so ~half were elected in 2018 — those
  currently get **no wealth** (`tse_sq = NULL`). `SENATOR_ELECTIONS` holds only the verified 2022
  entry; **do not add an unverified 2018 código**. Closing the gap means the TSE **bulk dataset**
  (`DATA-SOURCES.md`), not this API.
- The fetch is **best-effort**: a TSE outage or unmatched name yields zeros + `tse_sq = NULL`, and
  the card renders "Patrimônio não localizado no TSE" (driven by `tse_sq`), never a misleading
  R$ 0,00. Resolved senators feed `wealth_capital` into `score_keyword`, so the
  self-interest ("protege o próprio patrimônio") metric becomes real for them.

## 5. Where it lives

`app/senado.py`: `find_materia`, `fetch_votacoes`, `ingest_law`, `build_senado_package`,
`list_current_senators`, `resolve_senator`, `score_senator`. Scoring reuses
`score_candidate.{vote_class, score_keyword, infer_law_vote_from_cache(…, house='senado')}`.

```
CLI:    python app/senado.py --name "Alan Rick"
HTTP:   GET /api/senators/scorecard?name=Alan%20Rick
```
