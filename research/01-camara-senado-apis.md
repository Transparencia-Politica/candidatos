# Legislative Behavior Data — Câmara dos Deputados & Senado Federal Open-Data APIs

Research report for Candidato (Transparência-Política), a 2026 Brazilian Wahl-O-Mat-style voting-advice app. Scope: **legislative behavior only** (deputies, senators, roll-call votes, bills, attendance, expenses, topic taxonomies). TSE/election-candidate data is out of scope (handled separately).

All endpoints below were **verified live** against the production APIs on 2026-06-26. Status of each is noted. Both APIs are **open, require no API key, and impose no documented hard rate limit** (be polite: throttle to a few req/s and cache aggressively).

---

## Part 1 — Câmara dos Deputados (Dados Abertos API v2)

- **Base URL:** `https://dadosabertos.camara.leg.br/api/v2`
- **Interactive docs (Swagger):** <https://dadosabertos.camara.leg.br/swagger/api.html>
- **GitHub / issue tracker:** <https://github.com/CamaraDosDeputados/dados-abertos>
- **Postman collection:** <https://documenter.getpostman.com/view/8521432/TVCb4AVW>
- **Auth:** none (fully open). **Format:** JSON by default; send `Accept: application/xml` or append `?formato=xml` for XML. CSV available on some endpoints via `Accept: text/csv`.
- **Pagination model:** uniform across list endpoints. Query params `pagina` (1-based), `itens` (page size, max **100**), `ordem` (`ASC`/`DESC`), `ordenarPor` (field name). Every response wraps data in `{"dados":[...],"links":[...]}` where `links` contains HATEOAS `self/next/first/last` URLs — follow `rel:"next"` to paginate, or read total page count from the `last` link.
- **Update cadence:** near-real-time for the live API. Votes appear within minutes/hours of the session; expenses (CEAP) are updated as documents are reimbursed (effectively daily). The current legislature is **idLegislatura=57** (2023–2027).

### 1.1 Deputados (list + detail)

| Purpose | Endpoint |
|---|---|
| List | `GET /deputados` |
| Detail | `GET /deputados/{id}` |

**List params:** `idLegislatura` (e.g. `57` for current), `siglaUf`, `siglaPartido`, `siglaSexo`, `nome`, `pagina`, `itens`, `ordem`, `ordenarPor` (e.g. `nome`).

Example: <https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura=57&ordem=ASC&ordenarPor=nome&itens=100>

**List fields:** `id`, `uri`, `nome`, `siglaPartido`, `uriPartido`, `siglaUf`, `idLegislatura`, `urlFoto`, `email`. **The `id` is the master deputy identifier** that ties every other resource together (votes, expenses, speeches, events).

**Detail** (`/deputados/{id}`) adds `nomeCivil`, `cpf`, `dataNascimento`, `municipioNascimento`, `ufNascimento`, `escolaridade`, `gabinete`, `redeSocial`, and the current `ultimoStatus` (party, situation, condition).

Sub-resources of a deputy: `/deputados/{id}/despesas`, `/deputados/{id}/discursos`, `/deputados/{id}/eventos`, `/deputados/{id}/orgaos` (committees), `/deputados/{id}/frentes`, `/deputados/{id}/ocupacoes`, `/deputados/{id}/profissoes`, `/deputados/{id}/historico`.

### 1.2 Votações (roll-call votes) — list

`GET /votacoes` — **verified.** Returns the catalogue of vote events (plenary and committee).

**Params:** `id` (proposição id), `idProposicao`, `idEvento`, `idOrgao`, `dataInicio`, `dataFim` (`AAAA-MM-DD`), `pagina`, `itens`, `ordem`, `ordenarPor` (use `dataHoraRegistro`). Note: there is **no `siglaOrgao` filter** — filter the `siglaOrgao` field client-side (e.g. keep only `PLEN` for plenary).

Example (most recent first): <https://dadosabertos.camara.leg.br/api/v2/votacoes?ordem=DESC&ordenarPor=dataHoraRegistro&itens=100>

**Fields:** `id` (the **votação id**, format `"{proposicaoId}-{seq}"`, e.g. `"2473389-68"`), `uri`, `data`, `dataHoraRegistro`, `siglaOrgao` (`PLEN`, `CN`, committee codes…), `uriOrgao`, `uriEvento`, `proposicaoObjeto`, `uriProposicaoObjeto`, `descricao` (free-text describing what was decided and the Sim/Não tally), `aprovacao` (`1`=approved, `0`=rejected).

**Important:** many records (committee budget items, procedural `SECAP`/`CN` entries) are **symbolic votes with no nominal roll-call** — their `/votos` array is empty. Only a subset (mostly `PLEN` substantive votes) have individual votes. Filter for these by checking that `/votos` is non-empty.

**Votação detail:** `GET /votacoes/{id}` adds `votosSim`, `votosNao`, `votosOutros`, `ultimaApresentacaoProposicao`, and the list of `objetosPossiveis`/`proposicoesAfetadas`.

### 1.3 Votos — how each deputy voted (the core table)

`GET /votacoes/{id}/votos` — **verified.** **This endpoint is NOT paginated** — it returns the *complete* list of individual votes in one response (e.g. 446 votes for a full plenary vote). Passing `itens`/`pagina` returns HTTP 400. Do not paginate it.

Example: <https://dadosabertos.camara.leg.br/api/v2/votacoes/2473389-68/votos>

**Each element:**
```json
{
  "tipoVoto": "Não",
  "dataRegistroVoto": "2024-12-17T23:04:22",
  "deputado_": {
    "id": 204391, "nome": "José Nelto",
    "siglaPartido": "UNIÃO", "siglaUf": "GO", "idLegislatura": 57, ...
  }
}
```
`tipoVoto` values: **`Sim`, `Não`, `Abstenção`, `Obstrução`, `Artigo 17`** (Art.17 = the Speaker, votes only to break ties). `deputado_.id` links straight back to `/deputados/{id}`. This `(votacaoId, deputadoId, tipoVoto)` triple is the atomic unit for deriving positions.

### 1.4 Orientações de bancada (party-line guidance per vote)

`GET /votacoes/{id}/orientacoes` — **verified.** Returns how each party/bloc *instructed* its members to vote — invaluable for measuring party loyalty and for labelling a vote as "Government" vs "Opposition".

Example: <https://dadosabertos.camara.leg.br/api/v2/votacoes/2473389-68/orientacoes>

**Fields:** `orientacaoVoto` (`Sim`/`Não`/`Liberado`/`Obstrução`), `siglaPartidoBloco` (party acronym, or the pseudo-blocs **`Governo`**, **`Oposição`**, **`Minoria`**, **`Maioria`**), `codTipoLideranca`, `codPartidoBloco`. Comparing a deputy's `tipoVoto` against the `Governo`/`Oposição` orientation is the cleanest way to place them on a government-support axis without hand-coding each bill.

### 1.5 Proposições (bills) + authorship + themes

| Purpose | Endpoint |
|---|---|
| List | `GET /proposicoes` |
| Detail | `GET /proposicoes/{id}` |
| **Themes of a bill** | `GET /proposicoes/{id}/temas` |
| Authors | `GET /proposicoes/{id}/autores` |
| Related bills | `GET /proposicoes/{id}/relacionadas` |
| Procedural history | `GET /proposicoes/{id}/tramitacoes` |
| Votes on the bill | `GET /proposicoes/{id}/votacoes` |

**List params:** `siglaTipo` (`PL`, `PEC`, `PLP`, `MPV`, `PDL`…), `numero`, `ano`, `dataApresentacaoInicio`/`Fim`, `idDeputadoAutor`, `autor`, `siglaPartidoAutor`, `siglaUfAutor`, **`codTema`** (filter by theme code), `keywords`, plus pagination.

Example (environment bills, type PL, 2024): <https://dadosabertos.camara.leg.br/api/v2/proposicoes?codTema=48&siglaTipo=PL&ano=2024&itens=100>

**List fields:** `id` (**proposição id** — the number before the dash in a votação id), `uri`, `siglaTipo`, `codTipo`, `numero`, `ano`, `ementa` (summary), `dataApresentacao`.

**`/proposicoes/{id}/temas`** — **verified** — returns one row per assigned theme: `codTema`, `tema` (label), `relevancia`. A bill commonly has multiple themes (e.g. PL 182/2024 → codTema 70 *Finanças Públicas e Orçamento* + codTema 48 *Meio Ambiente*).

### 1.6 Theme taxonomy (codTema)

`GET /referencias/proposicoes/codTema` — **verified.** This is the official **closed list of ~33 policy themes**. Examples (cod → name):

| cod | Theme |
|---|---|
| 34 | Administração Pública |
| 40 | Economia |
| 43 | Direito Penal e Processual Penal |
| 44 | Direitos Humanos e Minorias |
| 46 | Educação |
| 48 | Meio Ambiente e Desenvolvimento Sustentável |
| 52 | Previdência e Assistência Social |
| 56 | Saúde |
| 57 | Defesa e Segurança |
| 58 | Trabalho e Emprego |
| 64 | Agricultura, Pecuária, Pesca e Extrativismo |
| 70 | Finanças Públicas e Orçamento |
| 74 | Política, Partidos e Eleições |
| 76 | Direito e Justiça |

Full list: <https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codTema>. Other reference lists live under `/referencias/...` (`/referencias/tiposProposicao`, `/referencias/situacoesProposicao`, etc.).

### 1.7 Eventos & presença (attendance)

- `GET /eventos` — list of sessions/meetings. Params: `dataInicio`, `dataFim`, `idTipoEvento`, `idOrgao`, pagination. Fields: `id`, `dataHoraInicio`, `descricaoTipo`, `descricaoSituacao`, `orgaos`.
- `GET /eventos/{id}` — detail.
- **Attendance:** `GET /eventos/{id}/deputados` — the list of deputies **present** at that event. There is **no single "attendance rate" endpoint**; attendance is derived by cross-referencing the events a deputy *should* attend (their committees + plenary) against the `/eventos/{id}/deputados` presence lists, or via `GET /deputados/{id}/eventos` (events tied to a deputy). For an authoritative attendance %, the Câmara's **frequência** is better taken from the bulk files (see §1.10) or the portal's *Infoleg*; the API gives the raw presence rows to compute it.

### 1.8 Discursos (speeches)

`GET /deputados/{id}/discursos` — speeches by a deputy. Params: `dataInicio`, `dataFim`, `ordenarPor=dataHoraInicio`, `ordem`, pagination. Fields: `dataHoraInicio`, `faseEvento`, `tipoDiscurso`, `keywords`, `sumario`, `transcricao`, `urlTexto`, `urlAudio`, `urlVideo`. Useful for NLP-based topic/stance signals to complement votes. (Note: returns empty for deputies with no logged speeches in the queried window.)

### 1.9 Frentes parlamentares (caucuses)

- `GET /frentes` — list (params: `idLegislatura`, pagination). Fields: `id`, `titulo`, `idLegislatura`.
- `GET /frentes/{id}` — detail (coordinator, etc.).
- `GET /frentes/{id}/membros` — members.
- `GET /deputados/{id}/frentes` — caucuses a deputy belongs to.

Membership in caucuses like *Frente Parlamentar da Agropecuária*, *Frente em Defesa da Vida e da Família*, *Frente Ambientalista* is a strong, cheap proxy for issue alignment (agribusiness, conservative/religious, environment) and can seed quiz-thesis mappings.

### 1.10 Despesas / CEAP (expenses)

`GET /deputados/{id}/despesas` — **verified.** The Cota para o Exercício da Atividade Parlamentar (parliamentary allowance). Params: `ano`, `mes`, `idLegislatura`, `cnpjCpfFornecedor`, pagination + `ordenarPor`.

Example: <https://dadosabertos.camara.leg.br/api/v2/deputados/204379/despesas?ano=2024&itens=100>

**Fields:** `ano`, `mes`, `tipoDespesa`, `codDocumento`, `tipoDocumento`, `dataDocumento`, `numDocumento`, `valorDocumento`, `urlDocumento` (link to the scanned receipt PDF), `nomeFornecedor`, `cnpjCpfFornecedor`, `valorLiquido`, `valorGlosa`, `numRessarcimento`. Useful as a transparency/accountability dimension, not a policy axis.

### 1.11 Bulk download files (`/arquivos/...`) vs the live API

For backfilling history and avoiding millions of paginated calls, use the **bulk dataset files** (CSV / JSON / XLSX / XML / Parquet via the Câmara's data lake). Pattern:

```
https://dadosabertos.camara.leg.br/arquivos/{dataset}/{formato}/{dataset}-{ano}.{formato}
```

Key files for this project:
- Deputies (all): <https://dadosabertos.camara.leg.br/arquivos/deputados/csv/deputados.csv>
- Votes by year: `…/arquivos/votacoes/csv/votacoes-2025.csv`
- **Individual votes by year (the big one):** `…/arquivos/votacoesVotos/csv/votacoesVotos-2025.csv` — every deputy's vote on every roll-call that year, joinable on `idVotacao` + `deputado_id`.
- Vote ↔ proposition link: `…/arquivos/votacoesProposicoes/csv/votacoesProposicoes-2025.csv`
- Vote orientations: `…/arquivos/votacoesOrientacoes/csv/votacoesOrientacoes-2025.csv`
- Propositions by year: `…/arquivos/proposicoes/csv/proposicoes-2025.csv`
- Proposition ↔ theme: `…/arquivos/proposicoesTemas/csv/proposicoesTemas-2025.csv`
- Proposition authors: `…/arquivos/proposicoesAutores/csv/proposicoesAutores-2025.csv`
- CEAP expenses by year: `…/arquivos/despesas/csv/despesas-2025.csv` (or per-deputy under `/arquivos/Ano-{ano}.csv` on the cota-parlamentar portal).

**Difference vs live API:** bulk files are **regenerated daily** (slightly less fresh than the live API), contain the **same fields**, use the **same identifiers**, and are the right tool for bulk/historical analytics. The live REST API is the right tool for on-demand lookups and the freshest data. The `arquivos` listing index is browsable at <https://dadosabertos.camara.leg.br/arquivos>.

### 1.12 How to derive a deputy's position on a topic (the join graph)

```
codTema ──< proposicoesTemas >── proposição(id) ──< votacoes(id = "{propId}-{seq}") ──< votos(tipoVoto, deputado_.id) >── deputado(id)
                                                              └── orientacoes(Governo/Oposição/party)
```
Recipe:
1. Pick the policy area → resolve to one or more `codTema` (e.g. environment = 48).
2. `GET /proposicoes?codTema=48` → set of bill `id`s (and/or use `/proposicoes/{id}/temas` to confirm relevance score).
3. For each bill, `GET /proposicoes/{id}/votacoes` → the votação `id`s that actually went to a roll-call.
4. `GET /votacoes/{votacaoId}/votos` → each deputy's `tipoVoto`; `…/orientacoes` → the Government/Opposition/party line.
5. Aggregate per deputy across the curated set of "thesis-defining" votes (hand-pick the votes that cleanly express each quiz thesis — agreement = Sim on a pro-thesis bill, etc.) to compute a position score per axis.

**Identifiers that tie it together:** deputy `id` (int), proposição `id` (int), votação `id` (string `"{propId}-{seq}"`), `codTema` (int). Party is `siglaPartido`; legislature is `idLegislatura` (57 current).

---

## Part 2 — Senado Federal (Dados Abertos)

- **Base URL:** `https://legis.senado.leg.br/dadosabertos`
- **HTML docs (legacy):** <https://legis.senado.leg.br/dadosabertos/docs/index.html>
- **Swagger UI (current):** <https://legis.senado.leg.br/dadosabertos/api-docs/swagger-ui/index.html>
- **OpenAPI 3.1 spec (machine-readable, 157 paths):** <https://legis.senado.leg.br/dadosabertos/v3/api-docs>
- **Auth:** none (open). **Format:** **XML is the default.** Get JSON either by appending `.json` to the path (legacy services, e.g. `/senador/5012.json`) **or** by sending `Accept: application/json` (works on the new services). Many legacy responses are deeply nested XML-style JSON (`{"DetalheParlamentar":{"Parlamentar":{...}}}`).

### ⚠️ Critical: the Senado migrated its legislative services in 2025

The classic services under `/materia/...`, `/senador/{id}/votacoes`, `/senador/{id}/autorias`, and `/plenario/votacao/nominal/...` are now **DEPRECATED** (marked `DataDepreciacao: 2025-03-18`, `DataDesativacaoCompleta: 2026-02-01`). They still respond today but **must not be built on for a 2026 product.** Use the **new replacement services**:

| Old (deprecated) | New (use this) |
|---|---|
| `/materia/{codigo}`, `/materia/{sigla}/{num}/{ano}` | **`/processo`** (list) and **`/processo/{id}`** (detail) |
| `/senador/{id}/votacoes`, `/materia/votacoes/{codigo}`, `/plenario/votacao/nominal/{ano}` | **`/votacao`** |
| `/senador/{id}/autorias` | `/processo?codigoParlamentarAutor={codigo}` (authorship via processo) |
| committee votes | **`/votacaoComissao/...`** |

### 2.1 Senadores (senators)

| Purpose | Endpoint | Status |
|---|---|---|
| In-exercise list | `GET /senador/lista/atual` | current ✅ |
| By legislature | `GET /senador/lista/legislatura/{leg}` (or `/{ini}/{fim}`) | current |
| On-leave | `GET /senador/afastados` | current |
| Detail | `GET /senador/{codigo}` | current ✅ |
| Mandates | `GET /senador/{codigo}/mandatos` | current |
| Committees | `GET /senador/{codigo}/comissoes` | current |
| Party affiliations | `GET /senador/{codigo}/filiacoes` | current |
| Speeches | `GET /senador/{codigo}/discursos` | current |
| Authorship | `GET /senador/{codigo}/autorias` | **deprecated** → use `/processo` |
| Votes | `GET /senador/{codigo}/votacoes` | **deprecated** → use `/votacao` |

Example: <https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json>

**List fields** (`ListaParlamentarEmExercicio.Parlamentares.Parlamentar[].IdentificacaoParlamentar`): `CodigoParlamentar` (**the senator id**), `CodigoPublicoNaLegAtual`, `NomeParlamentar`, `NomeCompletoParlamentar`, `SexoParlamentar`, `UrlFotoParlamentar`, `EmailParlamentar`, `SiglaPartidoParlamentar`, `UfParlamentar`, `Bloco` (`{CodigoBloco, NomeBloco}`), `MembroMesa`, `MembroLideranca`, plus a `Mandato` block. There are **81 senators** (3 per state + DF).

### 2.2 Votação (roll-call votes) — NEW unified service

`GET /votacao` — **verified.** This single endpoint returns nominal votes **with each parlamentar's vote nested inline**, so one call gives you the full roll-call (no second request needed).

**Params:** `dataInicio`, `dataFim` (`AAAA-MM-DD`), `idProcesso`, `codigoMateria`, `sigla`+`numero`+`ano` (e.g. `PLP/201/2019`), `codigoSessao`, `codigoParlamentar`, `nomeParlamentar`, `siglaVotoParlamentar`, `v` (service version).

Examples:
- By period: <https://legis.senado.leg.br/dadosabertos/votacao?dataInicio=2025-04-01&dataFim=2025-04-30>
- By bill: <https://legis.senado.leg.br/dadosabertos/votacao?sigla=PLP&numero=201&ano=2019>
- By senator (replaces deprecated `/senador/{id}/votacoes`): `…/votacao?codigoParlamentar=5012`

**Top-level fields per vote:** `idProcesso`, `codigoMateria`, `identificacao` (e.g. `"PLP 201/2019"`), `sigla`/`numero`/`ano`, `ementa`, `descricaoVotacao`, `dataSessao`, `codigoSessaoVotacao`, `resultadoVotacao`, `votacaoSecreta`, `totalVotosSim`/`Nao`/`Abstencao`, and **`votos`** (array). Each `votos[]` element: `codigoParlamentar`, `nomeParlamentar`, `siglaPartidoParlamentar`, `siglaUFParlamentar`, `sexoParlamentar`, **`siglaVotoParlamentar`** (`Sim`, `Não`, `Abstenção`, `NCom` = not present, etc.). `votacaoSecreta=true` means no individual votes are disclosed.

**Party-line orientation (still current):** `GET /plenario/votacao/orientacaoBancada/{dataInicio}/{dataFim}` (or `/{dataSessao}`) gives bloc orientation, analogous to the Câmara's `/orientacoes`.

**Committee votes:** `GET /votacaoComissao/comissao/{siglaComissao}`, `/votacaoComissao/materia/{sigla}/{numero}/{ano}`, `/votacaoComissao/parlamentar/{codigo}`.

### 2.3 Processo (bills/matters) — NEW service replacing `/materia`

`GET /processo` (list) and `GET /processo/{id}` (detail) — **verified.**

**Key params:** `sigla`, `numero`, `ano`, `idProcesso`, `codigoMateria` (legacy MATE code, bridges to old data), `tramitando` (`S`/`N`), `autor`, `codigoParlamentarAutor`, `termo` (free-text keyword), `dataInicioApresentacao`/`dataFimApresentacao`, `dataInicioDeliberacao`/`dataFimDeliberacao`, **`codAssuntoGeral`**, **`codAssuntoEspecifico`**, `siglaSituacao`, `numdias` (updated in last N days, max 30).

Example: <https://legis.senado.leg.br/dadosabertos/processo?ano=2025&sigla=PL&numero=1>

Fields include `codigoMateria`, `idProcesso`, `identificacao`, `ementa`, `autoria`, `casaIdentificadora`, `dataApresentacao`, `dataDeliberacao`, `dataSituacaoAtual`. `idProcesso` is the join key to `/votacao` (`idProcesso=`).

### 2.4 Subject taxonomy (assuntos) — the Senado's analogue to codTema

`GET /processo/assuntos` — **verified.** Returns a **two-level subject taxonomy**: each row has `id`, `assuntoGeral` (broad category: *Administrativo*, *Econômico*, *Social*, *Penal*, *Político*, etc.), `assuntoEspecifico` (specific subject), and validity dates. Filter bills with `codAssuntoGeral` / `codAssuntoEspecifico` on `/processo`.

Full list: <https://legis.senado.leg.br/dadosabertos/processo/assuntos>. Related reference lists: `/processo/classes`, `/processo/siglas`, `/processo/tipos-decisao`, `/processo/tipos-situacao`.

### 2.5 Attendance (Senado)

The Senado does not expose a clean per-senator attendance-rate endpoint either. Presence is reconstructed from plenary sessions and committee membership: use `GET /senador/{codigo}/comissoes` + session lists, or the `votos[].siglaVotoParlamentar = "NCom"` (não compareceu) signal in roll-call votes as a practical attendance proxy. The portal page <https://www12.senado.leg.br/transparencia> publishes official presence statistics for cross-checking.

### 2.6 Senado join graph

```
codAssuntoGeral/Especifico ──< /processo (idProcesso) >──< /votacao?idProcesso= (votos[].codigoParlamentar) >── /senador/{codigo}
                                                                    └── /plenario/votacao/orientacaoBancada (bloc line)
```
Identifiers: senator `CodigoParlamentar` (int), `idProcesso` (new int), `codigoMateria` (legacy int — bridges old↔new), assunto `id`. Party `SiglaPartidoParlamentar`, bloc `Bloco.CodigoBloco`.

### 2.7 Senado bulk data

The Senado publishes dataset listings at <https://www12.senado.leg.br/dados-abertos> and the catalog at <https://catalogodedadosabertos.com.br/Senado>. For roll-call backfill, paginating `/votacao` by month/year and persisting JSON is the pragmatic approach (there is no single all-votes CSV equivalent to the Câmara's `votacoesVotos-{ano}.csv`).

---

## Part 3 — Practical extraction recipe (copy-paste cURL)

All return JSON when called with `Accept: application/json` (Câmara JSON by default; Senado needs the header or `.json`).

**(a) List current deputies (Câmara, legislature 57):**
```bash
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura=57&ordem=ASC&ordenarPor=nome&itens=100&pagina=1"
```
→ `dados[]` of {id, nome, siglaPartido, siglaUf, …}; follow `links` `rel:next` (≈513 deputies → 6 pages of 100).

**(b) A recent roll-call and how each deputy voted (Câmara):**
```bash
# 1. find a vote
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/votacoes?ordem=DESC&ordenarPor=dataHoraRegistro&itens=20"
# 2. pull all individual votes (NOT paginated)
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/votacoes/2473389-68/votos"
# 3. party-line orientation for context
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/votacoes/2473389-68/orientacoes"
```
→ (2) returns the full array of `{tipoVoto, deputado_:{id,nome,siglaPartido,siglaUf}}`; (3) returns `{orientacaoVoto, siglaPartidoBloco}` including `Governo`/`Oposição`.

**(c) A deputy's events/attendance basis (Câmara):**
```bash
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/deputados/204379/eventos?dataInicio=2025-01-01&dataFim=2025-06-30&itens=100"
# and the presence list of a specific event:
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/eventos/{idEvento}/deputados"
```

**(d) A deputy's expenses (Câmara CEAP):**
```bash
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/deputados/204379/despesas?ano=2024&itens=100&ordem=DESC&ordenarPor=dataDocumento"
```
→ `dados[]` of {tipoDespesa, valorLiquido, nomeFornecedor, urlDocumento, …}.

**(e) Senado equivalent — current senators + a bill's roll-call:**
```bash
curl -H "Accept: application/json" \
  "https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json"
curl -H "Accept: application/json" \
  "https://legis.senado.leg.br/dadosabertos/votacao?dataInicio=2025-04-01&dataFim=2025-04-30"
```
→ second call returns each vote with nested `votos[]` ({codigoParlamentar, nomeParlamentar, siglaVotoParlamentar}). One call = full roll-call.

---

## Part 4 — Topic/theme classification for quiz-thesis mapping

**Yes — both houses expose an official subject taxonomy**, which is the backbone for mapping legislative behavior to quiz theses:

- **Câmara:** `codTema` — a flat list of ~33 themes (`/referencias/proposicoes/codTema`). Filter bills with `?codTema=`; read a bill's themes (with `relevancia`) from `/proposicoes/{id}/temas`. A bill can carry multiple themes.
- **Senado:** `assuntoGeral`/`assuntoEspecifico` — a two-level taxonomy (`/processo/assuntos`). Filter with `codAssuntoGeral` / `codAssuntoEspecifico` on `/processo`.

**Recommended approach to group bills into quiz policy areas:**

1. **Build a curated crosswalk** from your quiz axes → official codes. The two taxonomies don't share IDs, so maintain one mapping table per house. Example:

   | Quiz theme | Câmara codTema | Senado assuntoGeral/Especifico |
   |---|---|---|
   | Environment / climate | 48 (Meio Ambiente) | Social/Ambiental, "Meio ambiente" |
   | Public security / guns | 57 (Defesa e Segurança), 43 (Direito Penal) | Penal, "Segurança pública" |
   | Taxes / fiscal | 40 (Economia), 70 (Finanças Públicas) | Econômico, "Tributário"/"Orçamento" |
   | Labor rights | 58 (Trabalho e Emprego) | Social, "Trabalho" |
   | Minority/human rights, abortion | 44 (Direitos Humanos e Minorias), 56 (Saúde) | Social, "Direitos humanos"/"Saúde" |
   | Education | 46 (Educação) | Social, "Educação" |

2. **Don't rely on the taxonomy alone for sharp theses** (e.g. *abortion*, *gun ownership*, *gender* are not their own codTema). For those, combine `codTema` pre-filtering with **`keywords`/`termo` free-text search** and the bill `ementa`, and then **hand-pick the specific votações** that cleanly express each thesis. Quiz quality depends on a curated set of ~20–40 "signature votes", not on bulk theme aggregation.

3. **Augment with caucus membership** (`/frentes`, `/senador/{id}/comissoes`) and **party orientation** (`/orientacoes`, `/plenario/votacao/orientacaoBancada`) as priors — agribusiness-caucus or government-bloc membership predicts stance where roll-call data is thin.

4. **Derive a stance per axis**: for each curated vote, label the "agree-with-thesis" side (Sim or Não), then score each parlamentar = share of their votes aligning with the thesis (treat `Obstrução`/absence as a soft signal, `Abstenção` as neutral). This yields a per-deputy/per-senator position vector directly comparable to the user's quiz answers — the Wahl-O-Mat core.

---

## Summary of operational gotchas

1. **Câmara `/votos` is unpaginated** — returns the whole roll-call in one call (passing `itens` → HTTP 400).
2. **Most Câmara `/votacoes` rows have no nominal votes** — filter to those with a non-empty `/votos` (mostly `PLEN`).
3. **Senado's `/materia` and `/senador/{id}/votacoes` are deprecated (full shutdown scheduled 2026-02-01)** — build on `/processo` and `/votacao` instead.
4. **Senado defaults to XML** — always send `Accept: application/json` or append `.json`.
5. **Both APIs: open, no key, polite-rate, near-real-time live API + daily bulk files.** Cache and prefer bulk CSVs (Câmara `votacoesVotos-{ano}.csv`) for historical backfill.
6. **Join keys:** Câmara deputy `id` + proposição `id` + votação `id` (`"{propId}-{seq}"`) + `codTema`; Senado `CodigoParlamentar` + `idProcesso` (+ legacy `codigoMateria`) + assunto `id`.
