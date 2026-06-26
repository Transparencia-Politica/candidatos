# Candidato (Transparência-Política) — Data Sources & References

A Brazilian analog to Germany's [Wahl-O-Mat](https://www.wahl-o-mat.de/bw2026/app/main_app.html),
targeting the **2026 Brazilian general election** (President, Congress, governors,
state assemblies — election day **4 October 2026**).

The core idea: keep Wahl-O-Mat's thesis quiz for the *user*, but back each thesis with
**real legislative behavior** (how parties/candidates actually voted, showed up, authored
bills, and were funded) instead of self-reported manifesto answers.

---

## A. Official primary sources (the backbone)

### 1. Câmara dos Deputados — Dados Abertos
The single richest source. REST API + yearly bulk files (CSV / JSON / XLSX / XML).

- **API docs (Swagger):** https://dadosabertos.camara.leg.br/swagger/api.html
- **Portal:** https://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo
- **Announcement — detailed voting data:** https://www.camara.leg.br/assessoria-de-imprensa/641667-dados-abertos-disponibiliza-informacoes-detalhadas-de-votacoes/
- **Postman collection (community):** https://documenter.getpostman.com/view/8521432/TVCb4AVW

Per deputy you can pull:
- **Roll-call votes** (`votações nominais`) — exactly how each deputy voted on each bill.
  Bulk path: `http://dadosabertos.camara.leg.br/arquivos/votacoesVotos/{fmt}/votacoesVotos-{ano}.{fmt}`
- **Attendance** (`presença`) — who showed up to which session, daily-updated.
  Bulk path: `http://dadosabertos.camara.leg.br/arquivos/eventosPresencaDeputados/{fmt}/eventosPresencaDeputados-{ano}.{fmt}`
- **Bill authorship** (`proposições`), **speeches** (`discursos`), **parliamentary fronts** (`frentes`).
- **Expenses** — the CEAP "cota parlamentar" (every reimbursed expense, itemized).

### 2. Senado Federal — Dados Abertos
Same concept for the 81 senators: votes, matérias, attendance.

- **API docs (Swagger):** https://legis.senado.leg.br/dadosabertos/api-docs/swagger-ui/index.html

### 3. TSE — Tribunal Superior Eleitoral
The candidate / election layer. Covers the 2026 cycle.

- **Open Data Portal:** https://dadosabertos.tse.jus.br/
- **DivulgaCandContas (candidate + campaign finance lookup):** https://divulgacandcontas.tse.jus.br/
- **Campaign finance datasets:** https://dadosabertos.tse.jus.br/group/prestacao-de-contas-eleitorais
- **Candidate datasets:** https://dadosabertos.tse.jus.br/dataset/?q=candidatos
- **How-to guide (consulting candidates & accounts):** https://www.band.com.br/politica/eleicoes/2026/como-consultar-candidatos-e-contas-de-campanha-no-tse

Per candidate you can pull:
- **Declared assets** (`bens declarados`) — full patrimony list, comparable across cycles.
- **Campaign finance** — donors, suppliers, spending vs. legal limits.
- **Candidacy registration** — coalition, status, reasons for cassation, social-media handles,
  and government-plan documents (`proposta de governo`).

### 4. Portal da Transparência (federal government)
Federal spending, public-servant data, sanctions — useful for cross-referencing.

- **API:** https://portaltransparencia.gov.br/api-de-dados

---

## B. Curated / derived layers (save you the ETL)

### Base dos Dados
The big one: a cleaned, query-ready data lake (BigQuery) that already hosts Câmara, TSE, etc.
as tidy tables. Start here before scraping raw APIs.

- **Site:** https://basedosdados.org
- **Câmara dataset:** https://basedosdados.org/dataset/3d388daa-2d20-49eb-8f55-6c561bef26b6

### Basômetro (Estadão)
Government-support index — how aligned each party/deputy is with the executive on votes.
Good for an "independence vs. base loyalty" signal.

### Radar Parlamentar
Computes voting *similarity* between parties from roll-calls (PCA-style projection).
Lets you derive real ideological clustering instead of trusting manifestos.

### Operação Serenata de Amor / Jarbas + Rosie
ML auditing of CEAP expenses; flags suspicious reimbursements. Integrity signal.

- **Overview (Wikipedia):** https://en.wikipedia.org/wiki/Operation_Serenata_de_Amor
- **Case study:** https://rightscolab.org/case_study/operacao-serenata-de-amor/

### Brasil.io
Open datasets — candidacies, spending, company ownership, etc.

- **Site:** https://brasil.io

### brasil.vota.com — prior art (direct analog)
An existing Brazilian voting-guide / candidate-match product. Study as prior art for UX
and matching methodology.

- **Site:** https://brasil.vota.com/en/

---

## C. Context references

- **2026 Brazilian general election (Wikipedia):** https://en.wikipedia.org/wiki/2026_Brazilian_general_election
- **Opinion polling for the 2026 presidential election:** https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election

---

## D. How sources map to a matching pipeline

For each thesis, instead of one self-declared answer, compute a **behavioral score**
per party/candidate:

| Signal | Source | What it tells you |
|---|---|---|
| Roll-call votes on related bills | Câmara / Senado | Revealed position (vs. stated) |
| Attendance rate | Câmara / Senado presença | Engagement / reliability |
| Bill authorship & topics | Câmara proposições | What they actually prioritize |
| Gov-support alignment | Basômetro | Independence vs. base loyalty |
| Inter-party vote similarity | Radar Parlamentar | Real ideological clustering |
| Declared assets & campaign finance | TSE | Transparency / conflict signals |
| Expense anomalies | Serenata / Jarbas | Integrity flag |

**Design suggestion:** keep the ~38-thesis quiz for the user, but back each thesis with a
small bundle of real roll-call votes, so a party's "answer" is *computed* from how it
actually voted — not a press-office statement.

---

## E. MCP server references (architecture only — no electoral data)

Two "Brazil MCP" repos were evaluated. **Neither ships electoral, voting, attendance, or
candidate data** — they are Brazilian *utility-data* servers (CEP / CNPJ / PIX). Their value
is purely as architectural blueprints for building a future `dados-eleitorais` MCP server.
They are **not bundled** here — clone them from the GitHub URLs below to inspect their source.

### `impulsoxai/brazil-mcp-server` — production reference (Python)
- **Repo:** https://github.com/impulsoxai/brazil-mcp-server
- **Hosted endpoint:** https://mcp.impulsoxai.com.br/mcp
- Python 3.11+ / FastMCP, async, PostgreSQL, deployed on Railway. **25 tools** across 6 modules
  (CNPJ/CPF, CEP/address, PIX, holidays, currency, phone, agriculture).
- Worth copying: `ScopedFastMCP` tier-based access control, auth + rate-limit middleware,
  async `httpx` + TTL caching, `tools → services → models → middleware` layering, solid tests.
- Quality: ~8.5/10. **Best reference if building the elections server in Python.**

### `josenelsoncultri/josenelsoncultri-brazilinfo-mcp` — starter template (TypeScript)
- **Repo:** https://github.com/josenelsoncultri/josenelsoncultri-brazilinfo-mcp
- TypeScript / Node 24, MCP SDK + Zod, stdio transport, tsx (no build step). Single commit.
- **Only 1 live tool:** `search_zip_code` (ViaCEP). Advertised company-registration tool is unimplemented.
- Clean `domain / infrastructure / mcp` layering with DI, but thin (~120 LOC), happy-path tests only,
  no HTTP-error handling.
- Quality: ~7.5/10. **A clean skeleton to fork if building in TypeScript.**

### Third-party APIs used by those repos (general Brazilian data, not electoral)
- **BrasilAPI:** https://brasilapi.com.br
- **ViaCEP:** https://viacep.com.br
- **ExchangeRate-API:** https://open.er-api.com
- **INMET (weather):** https://apiprevmet3.inmet.gov.br
