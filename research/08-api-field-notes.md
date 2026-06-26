# API Field Notes — Hard-Won Gotchas (verified live)

Operational quirks discovered while building the POC (doc 07) and the research reports.
These cost real trial-and-error to find. Verified live 2026-06-26. Keep this current —
when an endpoint shape changes, fix it here.

---

## TSE — DivulgaCandContas REST (`divulgacandcontas.tse.jus.br/divulga/rest/v1`)

The biggest time-sink. The route shape is **not** intuitive and the segment order matters.

- **Headers are required.** Send a browser `User-Agent` **and** `Referer: https://divulgacandcontas.tse.jus.br/`. Without them you may get empty bodies / blocks.
- **List candidates** (works, but returns *summary* objects):
  ```
  /candidatura/listar/{ano}/{UF}/{idEleicao}/{cargo}/candidatos
  e.g. /candidatura/listar/2022/PE/2040602022/6/candidatos
  ```
  ⚠️ In the list response, **`bens`, `cpf`, `dataDeNascimento` etc. are `null`** — the list view
  does not populate assets. You must call the detail endpoint per candidate.
- **Candidate detail** (has `bens`, `totalDeBens`, `processosCassacao`, ficha-limpa flags,
  `arquivos`, `eleicoesAnteriores`):
  ```
  /candidatura/buscar/{ano}/{UF}/{idEleicao}/candidato/{SQ_CANDIDATO}
  e.g. /candidatura/buscar/2022/PE/2040602022/candidato/170001609112
  ```
  **Route-order trap (all verified):**
  | Route | Result |
  |---|---|
  | `buscar/{ano}/{UF}/{idEleicao}/candidato/{SQ}` | ✅ 200 (correct) |
  | `buscar/{ano}/{idEleicao}/{UF}/candidato/{SQ}` | ❌ 400 |
  | `buscar/{ano}/{UF}/{idEleicao}/{SQ}` (no `candidato`) | ❌ 404 |
  | `buscar/{ano}/{UF}/{idEleicao}/{cargo}/{SQ}` | ❌ 404 |
- **Key codes:** 2022 general election `idEleicao = 2040602022`; cargo `6 = Deputado Federal`
  (other cargos: 1 Presidente, 3 Governador, 5 Senador, 7 Dep. Estadual). UF is the 2-letter
  state (or `BR` for president).
- **The `id` field in the list = `SQ_CANDIDATO`** — the join key to use in the detail call.
- Assets come as `bens[]` with `descricaoDeTipoDeBem` + `valor` (string/number); sum them or use
  `totalDeBens`.
- Screening flags live on the detail object: `st_MOTIVO_FICHA_LIMPA`, `st_MOTIVO_ABUSO_PODER`,
  `st_MOTIVO_COMPRA_VOTO`, `processosCassacao`, `isCandidatoInapto`, `candidatoApto`.

## Câmara dos Deputados (`dadosabertos.camara.leg.br/api/v2`)

- **Open, no API key.** JSON by default; `{dados, links}` envelope; pagination via
  `pagina/itens/ordem/ordenarPor`.
- **`/votacoes/{id}/votos` is NOT paginated** — one call returns the entire roll-call (400+
  rows). Each row has `tipoVoto` (`Sim`/`Não`/`Abstenção`/`Obstrução`/`Artigo 17`) and a nested
  `deputado_` object — match on `deputado_.id`.
- **Most `/votacoes` rows are symbolic** with an empty `/votos` list — filter for non-empty
  before processing. Plenary nominal votes are the ones you want.
- **You cannot read a raw `Sim`/`Não` without context.** A vote on a *destaque* (amendment to
  suppress/keep text) means different things depending on the amendment. Always pull
  **`/votacoes/{id}/orientacoes`** (the Governo/Oposição/party line) to interpret direction.
- **Absence is common and is data**, not an error. A deputy simply doesn't appear in `/votos`
  for sessions they missed (see the Bivar PL 4173 case, doc 07). Model it; don't silently drop.
- Find a bill: `/proposicoes?siglaTipo=PL&numero=4173&ano=2023` → `id`; its votes:
  `/proposicoes/{id}/votacoes`. Theme taxonomy: `/referencias/proposicoes/codTema` (~33 themes)
  and filter `/proposicoes?codTema=...`.
- Expenses (CEAP): `/deputados/{id}/despesas?ano=YYYY` — paginated; sum `valorLiquido` across pages.

## Senado Federal (`legis.senado.leg.br/dadosabertos`)

- **XML by default** — send `Accept: application/json`.
- **Deprecation:** the classic `/materia` and `/senador/{id}/votacoes` services shut down
  **2026-02-01**. Use the new `/processo` (bills) and `/votacao` (roll-calls, with `votos[]`
  nested inline) services. OpenAPI at `/v3/api-docs`.

## Local tooling note

- The session shell is **zsh**, which does **not** word-split unquoted variable expansions
  (`set -- $var` won't split). For multi-field iteration, build the calls in Python (urllib) or
  use explicit arrays — don't rely on Bash-style word splitting.

## Cross-cutting

- **Rate-limit politely:** TSE IPs get blocked under load — add ≥0.3–1s between calls and a real
  User-Agent. Câmara tolerated rapid calls but be courteous.
- **The join key across systems is the person**, but the two systems use different ids: Câmara
  `deputado.id` vs TSE `SQ_CANDIDATO` (per election) / **CPF** (cross-cycle, when present).
  CPF is often masked in public TSE responses — plan a name+UF+birthdate fallback match.
